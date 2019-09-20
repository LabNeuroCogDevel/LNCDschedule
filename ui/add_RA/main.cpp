#include "add_ra.h"

#include <QApplication>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    add_ra w;
    w.show();
    return a.exec();
}
