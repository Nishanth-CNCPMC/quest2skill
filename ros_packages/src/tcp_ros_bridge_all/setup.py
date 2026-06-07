from glob import glob
from setuptools import find_packages, setup

package_name = "tcp_ros_bridge_all"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="ubuntu",
    maintainer_email="nishanthrajkumar1@gmail.com",
    description="Bridge Quest TCP JSON tracking and controls to ROS topics for Isaac.",
    license="MIT",
    extras_require={
        "test": [
            "pytest",
        ],
    },
    entry_points={
        "console_scripts": [
            "tcp_ros_bridge_all_node = tcp_ros_bridge_all.node:main",
        ],
    },
)
