from glob import glob
from setuptools import find_packages, setup


package_name = "tcp_ros_bridge"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/config", glob("config/*.yaml")),
        (f"share/{package_name}/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="ubuntu",
    maintainer_email="ubuntu@example.com",
    description="Bridge newline-delimited Quest TCP JSON payloads to ROS topics.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "tcp_ros_bridge_node = tcp_ros_bridge.node:main",
        ],
    },
)
