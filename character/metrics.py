from modules import shared
from prometheus_client import Info, Histogram, Counter, Gauge
from pynvml import *

nvmlInit()

i = Info('sd_character', 'Description of sd-character-extension')
i.info({
    'version': '1.0.3', 
    'name': shared.cmd_opts.character_server_name,
    'driver': nvmlSystemGetDriverVersion(),
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

# collect gpu usage every 10 seconds
gGPUUsedMemory = Gauge('gpu_memory_used_bytes', 'Memory used by the GPU device in bytes')
gGPUTotalMemory = Gauge('gpu_memory_total_bytes', 'Total memory of the GPU device in bytes')
gGPUTemperature = Gauge('gpu_temperature_celsius', 'Temperature of the GPU device in celsius')

def gpu_used_memory():
    nvmlInit()
    handle = nvmlDeviceGetHandleByIndex(0)
    meminfo = nvmlDeviceGetMemoryInfo(handle)
    nvmlShutdown()
    return meminfo.used

def gpu_total_memory():
    nvmlInit()
    handle = nvmlDeviceGetHandleByIndex(0)
    meminfo = nvmlDeviceGetMemoryInfo(handle)
    nvmlShutdown()
    return meminfo.total

def gpu_temperature():
    nvmlInit()
    handle = nvmlDeviceGetHandleByIndex(0)
    temperature = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)
    nvmlShutdown()
    return temperature

gGPUUsedMemory.set_function(gpu_used_memory())
gGPUTotalMemory.set_function(gpu_total_memory())
gGPUTemperature.set_function(gpu_temperature())

