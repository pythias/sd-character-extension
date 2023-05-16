from modules import shared
from prometheus_client import Info, Histogram, Counter, Gauge
from pynvml import *

nvmlInit()

totalMemory = 0
gpuCount = nvmlDeviceGetCount()
for i in range(gpuCount):
    handle = nvmlDeviceGetHandleByIndex(i)
    totalMemory += nvmlDeviceGetMemoryInfo(handle).total

i = Info('sd_character', 'Description of sd-character-extension')
i.info({
    'version': '1.0.3',
    'name': shared.cmd_opts.character_server_name,
    'driver': nvmlSystemGetDriverVersion(),
    'total_gpu_memory': f"{totalMemory}",
})

nvmlShutdown()

hT2I = Histogram('character_t2i_latency_seconds', 'Text to image latency')
hI2I = Histogram('character_i2i_latency_seconds', 'Image to image latency')
hDF = Histogram('character_face_latency_seconds', 'Detect face latency')
hDN = Histogram('character_nsfw_latency_seconds', 'Detect nsfw latency')
hTranslate = Histogram('character_translate_latency_seconds', 'Translate latency')

cT2I = Counter('character_t2i_requests', 'Text to image requests')
cI2I = Counter('character_i2i_requests', 'Image to image requests')

cT2IImages = Counter('character_t2i_images', 'Text to image images')
cI2IImages = Counter('character_i2i_images', 'Image to image images')

cFace = Counter('character_faces', 'Detect face')
cNSFW = Counter('character_nsfw', 'NSFW images')
cPrompts = Counter('character_prompts', 'Text to image prompts')
cNegativePrompts = Counter('character_negative_prompts', 'Text to image negative prompts')
cLoras = Counter('character_loras', 'Text to image loras')
cPixels = Counter('character_pixels', 'Text to image pixels')
cSteps = Counter('character_steps', 'Text to image steps')

gGPUUsedMemory = Gauge('gpu_memory_used_bytes', 'Memory used by the GPU device in bytes')
gGPUTemperature = Gauge('gpu_temperature_celsius', 'Temperature of the GPU device in celsius')
gGPUMemoryPercent = Gauge('gpu_memory_used_percent', 'Memory used by the GPU device in percent')

def gpu_used_memory():
    nvmlInit()
    used = 0
    for i in range(gpuCount):
        handle = nvmlDeviceGetHandleByIndex(i)
        info = nvmlDeviceGetMemoryInfo(handle)
        used += info.used
    nvmlShutdown()
    return used


def gpu_used_memory_percent():
    nvmlInit()
    used = 0
    for i in range(gpuCount):
        handle = nvmlDeviceGetHandleByIndex(i)
        info = nvmlDeviceGetMemoryInfo(handle)
        used += info.used
    nvmlShutdown()
    return (100 * used) / totalMemory


def gpu_temperature():
    nvmlInit()
    maxTemperature = 0
    for i in range(gpuCount):
        handle = nvmlDeviceGetHandleByIndex(i)
        temperature = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)
        maxTemperature = max(maxTemperature, temperature)
    nvmlShutdown()
    return maxTemperature

gGPUUsedMemory.set_function(gpu_used_memory)
gGPUTemperature.set_function(gpu_temperature)
gGPUMemoryPercent.set_function(gpu_used_memory_percent)
