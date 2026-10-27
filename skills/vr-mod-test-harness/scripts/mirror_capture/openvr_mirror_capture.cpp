// Record what the SteamVR compositor shows in each eye, without OBS, a desktop window or a person.
//
// A background OpenVR client (it never starts SteamVR, submits frames or reads input) opens each
// eye's mirror texture once (IVRCompositor::GetMirrorTextureD3D11), shrinks it on the GPU with a
// mip chain and reads back only the small level. Full eye images are several GB/s over the bus;
// a downscale of 16 is a few MB/s and keeps up with the game. Works for OpenXR games too, since
// the compositor mirrors whatever was submitted.
//
//   openvr_mirror_capture <absolute prefix> snap [downscale=4]
//       writes <prefix>_left.ppm and <prefix>_right.ppm (one frame per eye, for frame_check.py)
//   openvr_mirror_capture <absolute prefix> stream <seconds> [downscale=16]
//       records every new frame of both eyes until <seconds> pass or <prefix>.stop exists:
//         <prefix>.rgb    frames back to back, both eyes side by side, RGB 8-bit
//         <prefix>.times  one line per frame: milliseconds since start, local clock HH:MM:SS.mmm
//         <prefix>.json   {"width", "height", "eye_width", "downscale", "format"}
//       A frame is new when a sparse pixel sample differs from the last frame written (the
//       compositor shows each game frame more than once). Prints one JSON summary line at the end.
//
// Downscale is rounded up to a power of two (the mip level whose size is at most 1/downscale).
// SteamVR must already be running. The process never takes window focus.
#include <Windows.h>
#include <d3d11.h>
#include <dxgi.h>
#include <wrl/client.h>
#include <openvr.h>

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <string>
#include <thread>
#include <vector>

using Microsoft::WRL::ComPtr;

namespace {

bool is_bgra(DXGI_FORMAT f) {
    return f == DXGI_FORMAT_B8G8R8A8_UNORM || f == DXGI_FORMAT_B8G8R8A8_UNORM_SRGB || f == DXGI_FORMAT_B8G8R8A8_TYPELESS;
}
bool is_rgba(DXGI_FORMAT f) {
    return f == DXGI_FORMAT_R8G8B8A8_UNORM || f == DXGI_FORMAT_R8G8B8A8_UNORM_SRGB || f == DXGI_FORMAT_R8G8B8A8_TYPELESS;
}

// One eye's mirror, opened once and read many times.
struct MirrorEye {
    vr::IVRCompositor* compositor{};
    void* view{};
    ComPtr<ID3D11Texture2D> texture, mips, staging;
    ComPtr<ID3D11ShaderResourceView> mip_view;
    bool bgra{};
    unsigned level{}, width{}, height{};

    ~MirrorEye() { if (view) compositor->ReleaseMirrorTextureD3D11(view); }

    bool open(ID3D11Device* device, vr::IVRCompositor* c, vr::EVREye which, unsigned downscale, std::string& error) {
        compositor = c;
        if (c->GetMirrorTextureD3D11(which, device, &view) != vr::VRCompositorError_None || !view) {
            error = "GetMirrorTextureD3D11 failed"; return false;
        }
        ComPtr<ID3D11Resource> resource;
        static_cast<ID3D11ShaderResourceView*>(view)->GetResource(&resource);
        if (FAILED(resource.As(&texture))) { error = "mirror is not a 2D texture"; return false; }
        D3D11_TEXTURE2D_DESC desc{};
        texture->GetDesc(&desc);
        bgra = is_bgra(desc.Format);
        if (!bgra && !is_rgba(desc.Format)) { error = "unsupported mirror format " + std::to_string(desc.Format); return false; }
        while ((1u << level) < downscale) ++level;
        width = (std::max)(1u, desc.Width >> level);
        height = (std::max)(1u, desc.Height >> level);

        // A typeless copy with a mip chain, so GenerateMips can shrink it on the GPU.
        D3D11_TEXTURE2D_DESC chain = desc;
        chain.Format = bgra ? DXGI_FORMAT_B8G8R8A8_TYPELESS : DXGI_FORMAT_R8G8B8A8_TYPELESS;
        chain.MipLevels = level + 1;
        chain.ArraySize = 1;
        chain.SampleDesc = {1, 0};
        chain.Usage = D3D11_USAGE_DEFAULT;
        chain.BindFlags = D3D11_BIND_SHADER_RESOURCE | D3D11_BIND_RENDER_TARGET;
        chain.CPUAccessFlags = 0;
        chain.MiscFlags = D3D11_RESOURCE_MISC_GENERATE_MIPS;
        if (FAILED(device->CreateTexture2D(&chain, nullptr, &mips))) { error = "mip texture failed"; return false; }
        D3D11_SHADER_RESOURCE_VIEW_DESC srv{};
        srv.Format = bgra ? DXGI_FORMAT_B8G8R8A8_UNORM : DXGI_FORMAT_R8G8B8A8_UNORM;
        srv.ViewDimension = D3D11_SRV_DIMENSION_TEXTURE2D;
        srv.Texture2D.MipLevels = level + 1;
        if (FAILED(device->CreateShaderResourceView(mips.Get(), &srv, &mip_view))) { error = "mip view failed"; return false; }

        D3D11_TEXTURE2D_DESC copy = chain;
        copy.Width = width;
        copy.Height = height;
        copy.MipLevels = 1;
        copy.Usage = D3D11_USAGE_STAGING;
        copy.BindFlags = 0;
        copy.CPUAccessFlags = D3D11_CPU_ACCESS_READ;
        copy.MiscFlags = 0;
        if (FAILED(device->CreateTexture2D(&copy, nullptr, &staging))) { error = "staging texture failed"; return false; }
        return true;
    }

    // Writes width x height RGB pixels to `out`, rows `stride` bytes apart.
    bool read(ID3D11DeviceContext* context, uint8_t* out, size_t stride) {
        context->CopySubresourceRegion(mips.Get(), 0, 0, 0, 0, texture.Get(), 0, nullptr);
        if (level) context->GenerateMips(mip_view.Get());
        context->CopySubresourceRegion(staging.Get(), 0, 0, 0, 0, mips.Get(), level, nullptr);
        D3D11_MAPPED_SUBRESOURCE mapped{};
        if (FAILED(context->Map(staging.Get(), 0, D3D11_MAP_READ, 0, &mapped))) return false;
        for (unsigned y = 0; y < height; ++y) {
            const auto* row = static_cast<const uint8_t*>(mapped.pData) + size_t(y) * mapped.RowPitch;
            for (unsigned x = 0; x < width; ++x) {
                const uint8_t* p = row + size_t(x) * 4;
                uint8_t* q = out + size_t(y) * stride + size_t(x) * 3;
                q[0] = bgra ? p[2] : p[0];
                q[1] = p[1];
                q[2] = bgra ? p[0] : p[2];
            }
        }
        context->Unmap(staging.Get(), 0);
        return true;
    }
};

std::string local_clock() {
    SYSTEMTIME t{};
    GetLocalTime(&t);
    char text[16];
    std::snprintf(text, sizeof text, "%02u:%02u:%02u.%03u", t.wHour, t.wMinute, t.wSecond, t.wMilliseconds);
    return text;
}

bool open_eyes(ID3D11Device* device, ID3D11DeviceContext* context, unsigned downscale, MirrorEye (&eyes)[2]) {
    std::string error;
    auto* compositor = vr::VRCompositor();
    if (!eyes[0].open(device, compositor, vr::Eye_Left, downscale, error) ||
        !eyes[1].open(device, compositor, vr::Eye_Right, downscale, error)) {
        std::fprintf(stderr, "%s\n", error.c_str());
        return false;
    }
    if (eyes[0].width != eyes[1].width || eyes[0].height != eyes[1].height) {
        std::fprintf(stderr, "eye size mismatch\n");
        return false;
    }
    // The first copy from a freshly opened mirror can read black: read both eyes once and discard.
    std::vector<uint8_t> scratch(size_t(eyes[0].width) * eyes[0].height * 3);
    for (auto& eye : eyes) eye.read(context, scratch.data(), size_t(eye.width) * 3);
    return true;
}

int snap(const std::string& prefix, unsigned downscale, ID3D11Device* device, ID3D11DeviceContext* context) {
    MirrorEye eyes[2];
    if (!open_eyes(device, context, downscale, eyes)) return 1;
    const unsigned w = eyes[0].width, h = eyes[0].height;
    const char* names[2] = {"_left.ppm", "_right.ppm"};
    std::vector<uint8_t> pixels(size_t(w) * h * 3);
    for (int e = 0; e < 2; ++e) {
        if (!eyes[e].read(context, pixels.data(), size_t(w) * 3)) { std::fprintf(stderr, "read failed\n"); return 1; }
        std::ofstream file{prefix + names[e], std::ios::binary};
        file << "P6\n" << w << ' ' << h << "\n255\n";
        file.write(reinterpret_cast<const char*>(pixels.data()), std::streamsize(pixels.size()));
    }
    std::printf("{\"eye_width\":%u,\"eye_height\":%u,\"downscale\":%u}\n", w, h, 1u << eyes[0].level);
    return 0;
}

int stream(const std::string& prefix, double seconds, unsigned downscale, ID3D11Device* device, ID3D11DeviceContext* context) {
    MirrorEye eyes[2];
    if (!open_eyes(device, context, downscale, eyes)) return 1;
    const unsigned w = eyes[0].width, h = eyes[0].height;
    const size_t stride = size_t(w) * 2 * 3;
    std::vector<uint8_t> frame(stride * h), last;
    std::ofstream rgb{prefix + ".rgb", std::ios::binary}, times{prefix + ".times"};
    {
        std::ofstream info{prefix + ".json"};
        info << "{\"width\":" << w * 2 << ",\"height\":" << h << ",\"eye_width\":" << w
             << ",\"downscale\":" << (1u << eyes[0].level) << ",\"format\":\"rgb24\"}\n";
    }
    const std::filesystem::path stop{prefix + ".stop"};
    const auto start = std::chrono::steady_clock::now();
    auto next_stop_check = start;
    size_t written = 0, polled = 0;
    while (std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count() < seconds) {
        const auto now = std::chrono::steady_clock::now();
        if (now >= next_stop_check) {
            if (std::filesystem::exists(stop)) break;
            next_stop_check = now + std::chrono::milliseconds(500);
        }
        if (!eyes[0].read(context, frame.data(), stride) || !eyes[1].read(context, frame.data() + size_t(w) * 3, stride)) {
            std::fprintf(stderr, "read failed\n");
            return 1;
        }
        ++polled;
        bool changed = last.empty();
        for (size_t i = 0; !changed && i < frame.size(); i += 97) changed = frame[i] != last[i];
        if (changed) {
            rgb.write(reinterpret_cast<const char*>(frame.data()), std::streamsize(frame.size()));
            last = frame;
            ++written;
            const double ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - start).count();
            times << ms << ' ' << local_clock() << '\n';
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(4));
    }
    std::printf("{\"frames\":%zu,\"polled\":%zu,\"width\":%u,\"height\":%u}\n", written, polled, w * 2, h);
    return 0;
}

int usage() {
    std::fprintf(stderr,
        "usage: openvr_mirror_capture <absolute prefix> snap [downscale=4]\n"
        "       openvr_mirror_capture <absolute prefix> stream <seconds> [downscale=16]\n");
    return 2;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 3 || !std::filesystem::path{argv[1]}.is_absolute()) return usage();
    const std::string prefix = argv[1], mode = argv[2];
    double seconds = 0;
    int downscale = 0;
    if (mode == "snap" && argc <= 4) {
        downscale = argc > 3 ? std::atoi(argv[3]) : 4;
    } else if (mode == "stream" && (argc == 4 || argc == 5)) {
        seconds = std::atof(argv[3]);
        downscale = argc > 4 ? std::atoi(argv[4]) : 16;
        if (seconds <= 0 || seconds > 3600) return usage();
    } else {
        return usage();
    }
    if (downscale < 1 || downscale > 64) return usage();

    auto error = vr::VRInitError_None;
    vr::VR_Init(&error, vr::VRApplication_Background);
    if (error != vr::VRInitError_None) {
        std::fprintf(stderr, "VR_Init(Background) failed: %d (is SteamVR running?)\n", int(error));
        return 1;
    }
    // The mirror is shared from the headset's adapter: create the device there, not on adapter 0.
    int32_t adapter_index = -1;
    vr::VRSystem()->GetDXGIOutputInfo(&adapter_index);
    ComPtr<IDXGIFactory1> factory;
    ComPtr<IDXGIAdapter1> adapter;
    if (adapter_index >= 0 && SUCCEEDED(CreateDXGIFactory1(IID_PPV_ARGS(&factory))))
        factory->EnumAdapters1(UINT(adapter_index), &adapter);
    ComPtr<ID3D11Device> device;
    ComPtr<ID3D11DeviceContext> context;
    int status = 1;
    if (FAILED(D3D11CreateDevice(adapter.Get(), adapter ? D3D_DRIVER_TYPE_UNKNOWN : D3D_DRIVER_TYPE_HARDWARE, nullptr, 0,
                                 nullptr, 0, D3D11_SDK_VERSION, &device, nullptr, &context)))
        std::fprintf(stderr, "D3D11 device failed\n");
    else if (mode == "snap")
        status = snap(prefix, unsigned(downscale), device.Get(), context.Get());
    else
        status = stream(prefix, seconds, unsigned(downscale), device.Get(), context.Get());
    context.Reset();
    device.Reset();
    vr::VR_Shutdown();
    return status;
}
