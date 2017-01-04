#ifdef _WIN32
#  include <windows.h>
#endif

#ifdef __APPLE__
#  include <OpenGL/gl.h>
#else
#  include <GL/gl.h>
#endif

typedef const GLubyte* (*get_string)(GLenum);

int main(int argc, char **argv) {
#ifdef __APPLE__
  get_string x = glGetString;
  return x == 0;
#else
  glGetString(GL_VERSION);
  return 0;
#endif
}
