#ifndef ADD_RA_H
#define ADD_RA_H

#include <QMainWindow>

QT_BEGIN_NAMESPACE
namespace Ui { class add_ra; }
QT_END_NAMESPACE

class add_ra : public QMainWindow
{
    Q_OBJECT

public:
    add_ra(QWidget *parent = nullptr);
    ~add_ra();

private:
    Ui::add_ra *ui;
};
#endif // ADD_RA_H
