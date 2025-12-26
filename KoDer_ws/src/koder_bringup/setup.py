from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'koder_bringup'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Launch files
        (os.path.join('share', package_name, 'launch'), 
            glob(os.path.join('launch', '*.launch.py'))),
        # Config files (YAML)
        (os.path.join('share', package_name, 'config'), 
            glob(os.path.join('config', '*.yaml'))),
        # Config files (Lua)
        (os.path.join('share', package_name, 'config'), 
            glob(os.path.join('config', '*.lua'))),
        # ✅ ADD MAPS (CRITICAL FIX!):
        (os.path.join('share', package_name, 'maps'), 
            glob(os.path.join('maps', '*'))),  # Include ALL map files (.yaml + .pgm)
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Abraham-Na70',
    maintainer_email='your_email@domain.com',
    description='Bringup package for the Koder robot (Pi + ESP32 architecture).',
    license='Apache-2.0',
    
    # ✅ ADD ENTRY POINTS FOR PYTHON SCRIPTS:
    entry_points={
        'console_scripts': [
            'publish_map_odom_tf.py = koder_bringup.publish_map_odom_tf:main',
        ],
    },
)