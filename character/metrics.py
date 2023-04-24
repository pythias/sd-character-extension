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

hT2I = Histogram('t2i_latency_seconds', 'Text to image latency')
hDF = Histogram('df_latency_seconds', 'Detect face latency')
hDN = Histogram('dn_latency_seconds', 'Detect nsfw latency')

cT2I = Counter('t2i_requests', 'Text to image requests')
cT2ISuccess = Counter('t2i_success', 'Text to image success')
cT2INSFW = Counter('t2i_nsfw', 'Text to image nsfw')
cT2IImages = Counter('t2i_images', 'Text to image images')
cT2IPrompts = Counter('t2i_prompts', 'Text to image prompts')
cT2INegativePrompts = Counter('t2i_negative_prompts', 'Text to image negative prompts')
cT2ILoras = Counter('t2i_loras', 'Text to image loras')
cT2IPixels = Counter('t2i_pixels', 'Text to image pixels')
cT2ISteps = Counter('t2i_steps', 'Text to image steps')

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
