# DomainSearch

DomainSearch is an intuitive and powerful analysis tool which collects
informations about a given domain. These Informations will later be used to
evaluate the domain. Based on the evaluation a firewall for example can block
connections to bad domains.

It's part of my [bachelor thesis](http://andreas.kowasch.de/files/ak-bachelorarbeit.pdf) and an based on a previous thesis from **Alexander Waldeck** (https://github.com/CatCookie/DomainSearch).

## Table of contents

- [Installation](#installation)
- [Usage](#usage)
- [Documentation](#documentation)
- [Creators](#creators)
- [Copyright and license](#copyright-and-license)

## Installation

### Dependencies

#### Application

* python 3.4
* mariadb 10.0.15
* qt5 (only for the gui)
* pyqt5 (only for the gui)

#### Python packages

* dnspython3 (1.12.0)
* lxml (3.4.1)
* pyenchant (1.6.6)
* PyMySQL (0.6.3)
* python-nmap (0.3.4)
* pythonwhois (2.4.3)
* requests (2.5.1)


## Usage

### Server

    python3 DomainSearchServer/Server.py -h

![DomainSearch Server](images/Shell/DSServer_1.png)

### Scanner

    python3 DomainSearchScanner/Scanner.py

![DomainSearch Server](images/Shell/DSScanner_1.png)

### Reviewer

    python3 DomainSearchScanner/Reviewer.py

![DomainSearch Server](images/Shell/DSReviewer.png)

### Viewer

    python3 DomainSearchViewer/Viewer.py

### ViewerGUI

    python3 DomainSearchViewer/ViewerGUI.py

![DomainSearch Server](images/GUI/1_Domains.png)

## Creators

**Alexander Waldeck** (waldeck@hm.edu) - Version 1.0

**Andreas Kowasch** (kowasch@hm.edu) - Version 1.1

## Copyright and license

Code and documentation copyright 2011-2014 Alexander Waldeck and Andreas Kowasch. Code released under [the BSD license](LICENSE).
