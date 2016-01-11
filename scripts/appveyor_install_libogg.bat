curl -LO http://downloads.xiph.org/releases/ogg/libogg-1.3.2.zip
7z x -y libogg-1.3.2.zip

set SRCDIR=libogg-1.3.2
set PROJDIR=%SRCDIR%\win32\VS2010
msbuild %PROJDIR%\libogg_static.sln
mkdir %SRCDIR%\lib
copy %PROJDIR%\Win32\Debug\libogg_static.lib %SRCDIR%\lib\ogg.lib
