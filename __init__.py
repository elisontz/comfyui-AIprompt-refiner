# -*- coding: utf-8 -*-

# 延迟导入，避免在ComfyUI启动初期因文件未就绪而产生问题
def get_node_mappings():
    # 只导入 refiner 和 translator 两个核心节点
    from .refiner import NODE_CLASS_MAPPINGS as refiner_class, NODE_DISPLAY_NAME_MAPPINGS as refiner_display
    from .translator import NODE_CLASS_MAPPINGS as translator_class, NODE_DISPLAY_NAME_MAPPINGS as translator_display
    
    # 将所有节点的映射信息合并到一个总的字典中
    NODE_CLASS_MAPPINGS = {**refiner_class, **translator_class}
    NODE_DISPLAY_NAME_MAPPINGS = {**refiner_display, **translator_display}
    
    return NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# ComfyUI会调用这两个变量
NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS = get_node_mappings()

# 声明这个包对外暴露了哪些变量
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
