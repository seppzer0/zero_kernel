import pytest
from pathlib import Path

from zkb.core import KernelBuilder
from zkb.managers import ResourceManager


@pytest.mark.parametrize(
    "config, expected_defconfig",
    (
        (
            {"codename": "dumpling", "base": "los", "lkv": "4.4", "clean_kernel": False, "ksu": False},
            Path("lineage_oneplus5_defconfig")
        ),
        (
            {"codename": "cheeseburger", "base": "pa", "lkv": "4.14", "clean_kernel": False, "ksu": True},
            Path("vendor", "paranoid_defconfig")
        ),
        (
            {"codename": "dumpling", "base": "x", "lkv": "4.4", "clean_kernel": True, "ksu": True},
            Path("oneplus5_defconfig")
        ),
        (
            {"codename": "guacamoleb", "base": "los", "lkv": "4.14", "clean_kernel": True, "ksu": False},
            Path("lineage_sm8150_defconfig")
        ),
    )
)
def test__defconfig__check(config: dict[str, str], expected_defconfig: Path) -> None:
    """Test defconfig path definition."""
    t = KernelBuilder(**config, rmanager=ResourceManager())
    res_actual = t._defconfig
    res_expected = expected_defconfig
    assert res_actual == res_expected
