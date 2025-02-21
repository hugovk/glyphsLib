# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import logging

from glyphsLib.types import Transform

from .constants import GLYPHS_PREFIX, COMPONENT_INFO_KEY

logger = logging.getLogger(__name__)


def to_ufo_components(self, ufo_glyph, layer):
    """Draw .glyphs components onto a pen, adding them to the parent glyph."""
    pen = ufo_glyph.getPointPen()

    for index, component in enumerate(layer.components):
        pen.addComponent(component.name, component.transform)

        if component.anchor:
            if COMPONENT_INFO_KEY not in ufo_glyph.lib:
                ufo_glyph.lib[COMPONENT_INFO_KEY] = []
            ufo_glyph.lib[COMPONENT_INFO_KEY].append(
                {"name": component.name, "index": index, "anchor": component.anchor}
            )

    # data related to components stored in lists of booleans
    # each list's elements correspond to the components in order
    for key in ["alignment", "locked", "smartComponentValues"]:
        values = [getattr(c, key) for c in layer.components]
        if any(values):
            ufo_glyph.lib[_lib_key(key)] = values


def to_glyphs_components(self, ufo_glyph, layer):
    for comp in ufo_glyph.components:
        component = self.glyphs_module.GSComponent(comp.baseGlyph)
        component.transform = Transform(*comp.transformation)
        layer.components.append(component)

    for key in ["alignment", "locked", "smartComponentValues"]:
        if _lib_key(key) not in ufo_glyph.lib:
            continue
        # FIXME: (jany) move to using component identifiers for robustness
        values = ufo_glyph.lib[_lib_key(key)]
        for component, value in zip(layer.components, values):
            if value is not None:
                setattr(component, key, value)

    if COMPONENT_INFO_KEY in ufo_glyph.lib:
        for component_info in ufo_glyph.lib[COMPONENT_INFO_KEY]:
            component_index = component_info["index"]
            component = layer.components[component_index]
            if component.name == component_info["name"]:
                component.anchor = component_info["anchor"]
            else:
                logger.warning(
                    "Glyph {}, layer {}: The ComponentInfo says the component at index "
                    "{} is named '{}', but it is actually named '{}'. Skipping, anchor "
                    "placement might get lost.".format(
                        ufo_glyph.name,
                        layer.name,
                        component_index,
                        component_info["name"],
                        component.name,
                    )
                )


def _lib_key(key):
    key = key[0].upper() + key[1:]
    return f"{GLYPHS_PREFIX}components{key}"


AXES_LIB_KEY = GLYPHS_PREFIX + "smartComponentAxes"


def to_ufo_smart_component_axes(self, ufo_glyph, glyph):
    def _to_ufo_axis(axis):
        return {
            "name": axis.name,
            "bottomName": axis.bottomName,
            "bottomValue": axis.bottomValue,
            "topName": axis.topName,
            "topValue": axis.topValue,
        }

    if glyph.smartComponentAxes:
        ufo_glyph.lib[AXES_LIB_KEY] = [
            _to_ufo_axis(a) for a in glyph.smartComponentAxes
        ]


def to_glyphs_smart_component_axes(self, ufo_glyph, glyph):
    def _to_glyphs_axis(axis):
        res = self.glyphs_module.GSSmartComponentAxis()
        res.name = axis["name"]
        res.bottomName = axis["bottomName"]
        res.bottomValue = axis["bottomValue"]
        res.topValue = axis["topValue"]
        res.topName = axis["topName"]
        return res

    if AXES_LIB_KEY in ufo_glyph.lib:
        glyph.smartComponentAxes = [
            _to_glyphs_axis(a) for a in ufo_glyph.lib[AXES_LIB_KEY]
        ]
