# SPDX-License-Identifier: GPL-2.0-or-later
"""Translations for the custom build's light and shadow linking UI."""
import bpy

_messages = {
    "Light Linking": "灯光链接",
    "Shadow Linking": "阴影链接",
    "Light Linking Specials": "灯光链接操作",
    "Shadow Linking Specials": "阴影链接操作",
    "New Light Linking Collection": "新建灯光链接集合",
    "New Shadow Linking Collection": "新建阴影链接集合",
    "Create new light linking collection used by the active emitter": "为活动灯光新建接收光照的物体集合",
    "Create new shadow linking collection used by the active emitter": "为活动灯光新建参与投影的物体集合",
    "Select Light Linking Receivers": "选择接收光照的物体",
    "Select Light Linking Blockers": "选择参与投影的物体",
    "Select all objects which receive light from this emitter": "选择灯光链接集合中的接收物体",
    "Select all objects which block light from this emitter": "选择阴影链接集合中的遮挡物体",
    "Link Receivers to Emitter": "将物体加入灯光链接",
    "Link Blockers to Emitter": "将物体加入阴影链接",
    "Light link selected receivers to the active emitter object": "将选中的物体加入活动灯光的灯光链接集合",
    "Light link selected blockers to the active emitter object": "将选中的物体加入活动灯光的阴影链接集合",
    "Include selected receivers to receive light from the active emitter": "允许所选物体接收活动灯光的光照",
    "Exclude selected receivers from receiving light from the active emitter": "排除活动灯光对所选物体的直接光照",
    "Include selected blockers to cast shadows from the active emitter": "允许所选物体为活动灯光投下阴影",
    "Exclude selected blockers from casting shadows from the active emitter": "排除所选物体为活动灯光投下的阴影",
    "Remove From Light Linking Collection": "从链接集合移除",
    "Remove this object or collection from the light linking collection": "移除选中的链接条目，不删除场景中的物体或集合",
    "Active object must be a light to share linking collections": "请最后选中源灯光，再关联链接集合",
    "Link Light Linking Collections": "关联灯光链接集合",
    "Link Shadow Linking Collections": "关联阴影链接集合",
    "Link Light and Shadow Linking Collections": "关联灯光与阴影链接集合",
    "Share the active light's receiver collection with selected editable lights":
        "让选中的可编辑灯光共用活动灯光的灯光链接集合",
    "Share the active light's blocker collection with selected editable lights":
        "让选中的可编辑灯光共用活动灯光的阴影链接集合",
    "Share both linking collections from the active light with selected editable lights":
        "让选中的可编辑灯光共用活动灯光的灯光链接与阴影链接集合",
}


def register():
    bpy.app.translations.unregister(__name__)
    bpy.app.translations.register(__name__, {
        'zh_CN': {(context, text): translation
                  for text, translation in _messages.items()
                  for context in ('*', 'Operator')},
    })


def unregister():
    bpy.app.translations.unregister(__name__)
