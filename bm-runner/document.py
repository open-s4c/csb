# Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
# SPDX-License-Identifier: MIT

import inspect
from config.application import Application, Adapter
from config.benchmark import BenchmarkConfig, MonitorType, ExecutionType
from config.container import ContainersConfig
from config.plugin import Plugin, ExecutionTime
from config.plot import PlotConfig, PlotType
from config.list import ListConfig, RangeConfig
from config.nics import NicsConfig
from typing import get_origin, get_args
from typing import Union, Optional
from bm_config import CampaignConfig
from config.env_config import UniversalConfig
import sys
import re

g_enums = [MonitorType, PlotType, ExecutionTime, ExecutionType]
g_sub_types = [Adapter, ListConfig, RangeConfig]
# main types are those that exist directly in JSON and have a CONFIG_KEY defined
g_main_types = [BenchmarkConfig, Application, ContainersConfig, Plugin, PlotConfig, NicsConfig]
main_config = CampaignConfig


# The documentation generation depends on adding the following template to the docstring of classes and enums:
# For classes:
# Add the following to the class __init__ docstring:
# """
# Class description
# Parameters
# ----------
# param1: description of param1
# param2: description of param2
# -
# """
# For enums:
# Add the following to the enum docstring:
# """
# Enum description
# Members
# ----------
# member1: description of member1
# member2: description of member2
# """
# """
# bm_config description
# Components
# ----------
# component1: description of component1
# component2: description of component2
# """


def pretty_type(t):
    origin = get_origin(t)
    args = get_args(t)

    # Optional[T] is represented as Union[T, NoneType]
    if origin is Union and type(None) in args:
        non_none = [a for a in args if a is not type(None)][0]
        return f"{pretty_type(non_none)}"

    # Generic types like list[int], dict[str, float]
    if origin:
        inner = ", ".join([pretty_type(a) for a in args])
        return f"{origin.__name__}[{inner}]"

    if hasattr(t, "__name__") and (t in g_sub_types or t in g_enums or t in g_main_types):
        # add anchor
        return f"[{t.__name__}](#{str(t.__name__).lower()})"

    # Normal classes
    if hasattr(t, "__name__"):
        return t.__name__

    return str(t)


def enum_values(t, add_title=True):
    documentation = f"## {t.__name__}\n" if add_title else ""
    doc_str = inspect.getdoc(t)
    documentation += get_enum_doc(doc_str) if doc_str else ""
    documentation += "<br/>Supported values:\n"
    for member in t:
        pattern = f"^{member.name}:(.*)"
        if doc_str:
            match = re.search(pattern, doc_str, re.MULTILINE)
            desc = match.group(1) if match else ""
        else:
            desc = ""
        documentation += f'- `"{member.value}"`: {desc}\n'
    return documentation


# looks for documentation of the given param
def get_description(doc: str, param):
    pattern = f"^{param}:.*\n((?:\s+.*\n)+)"
    match = re.search(pattern, doc, re.MULTILINE)
    if match:
        desc = match.group(1)
        return desc.replace("\n", " ")
    else:
        return "error"


def get_pretty_default(doc: Optional[str], param, default):
    if doc is None:
        doc = ""

    pattern = f"^{param}:.*= (.*)\n"
    match = re.search(pattern, doc, re.MULTILINE)
    if match:
        desc = match.group(1)
        return f"`{desc}`"
    else:
        return f"`{default}`" if default is not None and default != "" else ""


def get_header_doc(doc: str):
    pattern = "((?:.*\n)+)Parameters"
    match = re.search(pattern, doc, re.MULTILINE)
    if match:
        desc = match.group(1)
        return desc.replace("\n", " ")
    else:
        return ""


def get_enum_doc(doc: str):
    pattern = "((?:.*\n)+)Members"
    match = re.search(pattern, doc, re.MULTILINE)
    if match:
        desc = match.group(1)
        return desc.replace("\n", " ")
    else:
        return ""


def get_bm_config_doc(doc: str):
    pattern = "((?:.*\n)+)Components"
    match = re.search(pattern, doc, re.MULTILINE)
    if match:
        desc = match.group(1)
        return desc.replace("\n", " ")
    else:
        return ""


def get_components_default(doc: str):
    # If no match exists, this returns []
    pattern = "^(.*): (.*)"
    return re.findall(pattern, doc, re.MULTILINE)


# dumps the __init__ arguments of the given class
def dump_doc(cls):
    doc = None
    sig = inspect.signature(cls.__init__)
    # add class name as a header
    documentation = f"\n## {cls.__name__}\n"

    if cls.__init__.__doc__:
        doc = inspect.getdoc(cls.__init__)
        documentation += "" if doc is None else get_header_doc(doc) + "\n"

    params = sig.parameters

    # Show json key if exists
    if hasattr(cls, "CONFIG_KEY"):
        json_key = getattr(cls, "CONFIG_KEY")
        documentation += f'<br/>***JSON key: "{json_key}"***\n'

    documentation += "|Field|Type|Optional|Default|Description|\n"
    documentation += "|---|---|---|---|---|\n"

    for name, p in params.items():
        if name == "self":
            continue

        # determine if the field/key is optional
        if p.default is inspect._empty:
            optional = ":x:"
            default = ""
        else:
            optional = ":white_check_mark:"
            default = get_pretty_default(doc, name, p.default)

        desc = "" if doc is None else get_description(doc, name)
        documentation += f"|{name}|{pretty_type(p.annotation)}|{optional}|{default}|{desc}|\n"

    return documentation


def overall_main_doc(main_config):
    documentation = ""

    if main_config.__init__.__doc__:
        doc = inspect.getdoc(main_config.__init__)
        documentation += "" if doc is None else get_bm_config_doc(doc) + "\n"

        documentation += "|Type|Optional|JSON Representation|\n"
        documentation += "|---|---|---|\n"

        components = get_components_default(doc if doc is not None else "")

        for _, comp in components:
            # TODO: Improve code by search for signature of "__parse_{var}"
            if "Optional" in comp:
                optional = ":white_check_mark:"

                tmp = re.search("Optional\[(.*)\]", comp)
                name = tmp.group(1) if tmp is not None else "error"
            else:
                optional = ":x:"
                name = comp.strip()

            if "list" in name:
                represent = "`[...]`"

                tmp = re.search("list\[(.*)\]", name)
                name = tmp.group(1) if tmp is not None else "error"
            else:
                represent = "`{...}`"

            cls = None
            for t in g_main_types:
                if t.__name__ == name:
                    cls = t
                    break

            documentation += f"|{pretty_type(cls)}|{optional}|{represent}|\n"
    return documentation


def document_env_config():
    documentation = "## Environment Variables\n"
    documentation += enum_values(UniversalConfig, add_title=False)
    return documentation


if __name__ == "__main__":
    fname = sys.argv[1] if len(sys.argv) > 1 else "../doc/bm-config.md"
    documentation = ""

    documentation += "# Overall Configuration\n"
    documentation += overall_main_doc(main_config)

    # add sections for main types
    for t in g_main_types:
        documentation += dump_doc(t)

    documentation += "# Types\n"

    # add sections for subtypes
    for t in g_sub_types:
        documentation += dump_doc(t)

    # add enum sections
    for e in g_enums:
        documentation += enum_values(e)

    documentation += document_env_config()

    with open(fname, "w") as f:
        f.write(documentation)
