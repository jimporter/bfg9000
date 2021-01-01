#ifndef WINDOW_HPP
#define WINDOW_HPP

#include <QWidget>

namespace Ui {
  class MyWidget;
}

class Window : public QWidget {
  Q_OBJECT
public:
  explicit Window(QWidget *parent = 0);
  virtual ~Window();
private slots:
 void on_mybutton_clicked(bool checked);
private:
  Ui::MyWidget *ui_;
};

#endif
