// AGPL-3.0: streaming SHA-256 using the Windows cryptographic provider.
#include <windows.h>
#include <bcrypt.h>
#include <array>
#include <vector>

struct Resources {
    HANDLE file = INVALID_HANDLE_VALUE;
    BCRYPT_ALG_HANDLE algorithm = nullptr;
    BCRYPT_HASH_HANDLE hash = nullptr;
    ~Resources() {
        if (hash) BCryptDestroyHash(hash);
        if (algorithm) BCryptCloseAlgorithmProvider(algorithm, 0);
        if (file != INVALID_HANDLE_VALUE) CloseHandle(file);
    }
};

extern "C" __declspec(dllexport) int __cdecl hash_file_sha256(
    const wchar_t* path, unsigned char* output, unsigned long capacity) noexcept {
    if (!path || !output || capacity != 32) return 1;
    try {
        Resources resource;
        resource.file = CreateFileW(path, GENERIC_READ, FILE_SHARE_READ, nullptr,
                                   OPEN_EXISTING, FILE_FLAG_SEQUENTIAL_SCAN, nullptr);
        if (resource.file == INVALID_HANDLE_VALUE) return 2;
        if (BCryptOpenAlgorithmProvider(&resource.algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) < 0) return 3;
        if (BCryptCreateHash(resource.algorithm, &resource.hash, nullptr, 0, nullptr, 0, 0) < 0) return 3;
        std::vector<unsigned char> buffer(1024 * 1024);
        DWORD count = 0;
        for (;;) {
            if (!ReadFile(resource.file, buffer.data(), static_cast<DWORD>(buffer.size()), &count, nullptr)) return 4;
            if (!count) break;
            if (BCryptHashData(resource.hash, buffer.data(), count, 0) < 0) return 3;
        }
        return BCryptFinishHash(resource.hash, output, capacity, 0) < 0 ? 3 : 0;
    } catch (...) { return 5; }
}
