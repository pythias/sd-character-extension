from ast import Param


Name = "Character"

ParamExtra = "character_extra"
ParamFromUI = "from_webui"
ParamMultiEnabled = "multi_enabled"
ParamMultiCount = "multi_count"
ParamMultiSameSeed = "multi_same_seed"
ParamImage = "image_i2i"
ParamTryOnCloth = "image_tryon_cloth"
ParamTryOnModel = "image_tryon_model"
ParamControlNet0 = "image_cn_0"
ParamIgnoreCaption = "ignore_caption"

# 物品识别和重绘
ParamSegmentLabels = "segment_labels"
ParamSegmentErase = "segment_erase"

ParamFormat = "response_format"

# 年龄
ParamIgnoreAge = "ignore_age"

# 扩展参数名字
ExtraImageCaption = "image-caption"
ExtraHasIllegalWords = "has-illegal-words"

# 各种组件
ExNameT2I = "Character Text2Image"
ExNameI2I = "Character Image2Image"
ExNameTryOn = "Character TryOn"
ExNameEffects = "Character Effects"
ExNameInfo = "Character Info"

# 各种组件的执行顺序
ExIndexInfo = -1
ExIndexEffects = -2
ExIndexTryOn = -3
ExIndexFaceEditor = -4