import QtQuick 2.0
import QtQuick.Controls 1.0

ApplicationWindow {
  title: qsTr("Hello, world!")
  width: 150
  height: 100
  visible: true

  Button {
    text: qsTr("Hello, world!")
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.verticalCenter: parent.verticalCenter
  }
}
