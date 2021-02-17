#include "window.hpp"

#include <QPushButton>

#include "ui_widget.h"

Window::Window(QWidget *parent) : QWidget(parent) {
  ui_ = new Ui::MyWidget;
  ui_->setupUi(this);
}

Window::~Window() {
  delete ui_;
}

void Window::on_mybutton_clicked(bool checked) {
  ui_->mybutton->setText(checked ? "Checked" : "Hello, world!");
}
