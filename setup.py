import sys
import os
import traceback
import subprocess

from distutils.core import setup, Extension
from distutils.log import debug
from numpy.distutils.misc_util import get_numpy_include_dirs


# Windows checks
is_win = sys.platform.startswith("win")
is_win64 = (is_win and (os.environ["PROCESSOR_ARCHITECTURE"] == "AMD64"))
is_msvc = (is_win and sys.version_info[0] >= 2 and sys.version_info[1] >= 6)
is_mingw = (is_win and not is_msvc)

# Windows support functions
def find_javahome():
    """Find JAVA_HOME if it doesn't exist"""
    if os.environ.has_key('JAVA_HOME'):
        return os.environ['JAVA_HOME']
    if sys.platform == 'darwin':
        return "Doesn't matter"
    if is_win:
        import _winreg
        java_key_path = 'SOFTWARE\\JavaSoft\\Java Runtime Environment'
        looking_for = java_key_path
        try:
            kjava = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, java_key_path)
            looking_for = java_key_path + "\\CurrentVersion"
            kjava_values = dict([_winreg.EnumValue(kjava, i)[:2]
                                 for i in range(_winreg.QueryInfoKey(kjava)[1])])
            current_version = kjava_values['CurrentVersion']
            looking_for = java_key_path + '\\' + current_version
            kjava_current = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                                            looking_for)
            kjava_current_values = dict([_winreg.EnumValue(kjava_current, i)[:2]
                                         for i in range(_winreg.QueryInfoKey(kjava_current)[1])])
            return kjava_current_values['JavaHome']
        except:
            traceback.print_exc()
            sys.stderr.write("Failed to find registry entry: %s\n" %looking_for)
            return None

def find_jdk():
    """Find the JDK under Windows"""
    if sys.platform == 'darwin':
        return "Doesn't matter"
    if is_win:
        import _winreg
        jdk_key_path = 'SOFTWARE\\JavaSoft\\Java Development Kit'
        kjdk = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, jdk_key_path)
        kjdk_values = dict([_winreg.EnumValue(kjdk, i)[:2]
                             for i in range(_winreg.QueryInfoKey(kjdk)[1])])
        current_version = kjdk_values['CurrentVersion']
        kjdk_current = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                                       jdk_key_path + '\\' + current_version)
        kjdk_current_values = dict([_winreg.EnumValue(kjdk_current, i)[:2]
                                    for i in range(_winreg.QueryInfoKey(kjdk_current)[1])])
        return kjdk_current_values['JavaHome']

include_dirs = get_numpy_include_dirs()
extra_link_args = None
libraries = None
library_dirs = None

java_home = find_javahome()
debug("Using java_home = %s"%java_home)
jdk_home = find_jdk()
debug("Using jdk_home = %s"%jdk_home)

extra_sources=[]
if sys.platform == 'darwin':
        include_dirs += ['/System/Library/Frameworks/JavaVM.framework/Headers']
        extra_link_args = ['-framework', 'JavaVM']
elif is_win:
        if jdk_home is not None:
            jdk_include = os.path.join(jdk_home, "include")
            jdk_include_plat = os.path.join(jdk_include, sys.platform)
            include_dirs += [jdk_include, jdk_include_plat]
        if is_mingw:
            #
            # Build libjvm from jvm.dll on Windows.
            # This assumes that we're using mingw32 for build
            #
            cmd = ["dlltool", "--dllname", 
                   os.path.join(jdk_home,"jre\\bin\\client\\jvm.dll"),
                   "--output-lib","libjvm.a",
                   "--input-def","jvm.def",
                   "--kill-at"]
            p = subprocess.Popen(cmd)
            p.communicate()
            library_dirs = [os.path.abspath(".")]
        else:
            #
            # Use the MSVC lib in the JDK
            #
            jdk_lib = os.path.join(jdk_home, "lib")
            library_dirs = [jdk_lib]
            extra_sources = ["javabridge/strtoull.c"]
        libraries = ["jvm"]
elif sys.platform.startswith('linux'):
    include_dirs += [os.path.join(java_home,'include'),
                     os.path.join(java_home,'include','linux')]
    library_dirs = [os.path.join(java_home,'jre','lib','amd64','server')]
    libraries = ["jvm"]

jbridge = Extension("javabridge.javabridge", 
                    ["javabridge/javabridge.c"] + extra_sources,
                    libraries=libraries,
                    library_dirs=library_dirs,
                    include_dirs=include_dirs,
                    extra_link_args=extra_link_args)

# from http://packages.python.org/an_example_pypi_project/setuptools.html
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

print "DEBUG", sys.argv
print jbridge.sources

setup(name="javabridge",
      version="0.2",
      keywords="java native interface jni",
      long_description=read('README.txt'),
      url="https://github.com/thouis/Python-Java-Bridge",
      description="python wrapper for the Java Native Interface",
      maintainer="Thouis Jones",
      maintainer_email="thouis.jones@curie.fr",
      packages=['javabridge'],
      package_data={'javabridge': ['*.class']},
      ext_modules=[jbridge],
      classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Java',
        'Topic :: Software Development :: Libraries :: Java Libraries',])
