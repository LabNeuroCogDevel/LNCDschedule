#include "add_ra.h"
#include "ui_add_ra.h"

add_ra::add_ra(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::add_ra)
{
    ui->setupUi(this);
}

add_ra::~add_ra()
{
    delete ui;
}

