# Maintainer: Julian / Linux Community
pkgname=recomp-center
pkgver=1.0.0
pkgrel=1
pkgdesc="Modernes Recomp & Decomp Center zum Herunterladen, Aktualisieren und Verwalten nativer PC-Ports"
arch=('any')
url="https://github.com/recomp-center/recomp-center"
license=('GPL-3.0-or-later')
depends=(
    'python'
    'python-pyqt6'
    'xdg-utils'
)
optdepends=(
    'git: Zum Klonen von Source-Decompilierungs-Repositories'
)
source=()
sha256sums=()

package() {
    cd "$srcdir/.."
    install -d "$pkgdir/usr/share/recomp-center"
    install -d "$pkgdir/usr/bin"
    install -d "$pkgdir/usr/share/applications"
    install -d "$pkgdir/usr/share/icons/hicolor/128x128/apps"

    cp -r recomp_center "$pkgdir/usr/share/recomp-center/"
    cp main.py "$pkgdir/usr/share/recomp-center/"
    
    install -Dm755 recomp-center "$pkgdir/usr/bin/recomp-center"
    install -Dm644 recomp-center.desktop "$pkgdir/usr/share/applications/recomp-center.desktop"
    
    if [ -f "recomp-center.png" ]; then
        install -Dm644 recomp-center.png "$pkgdir/usr/share/icons/hicolor/128x128/apps/recomp-center.png"
    fi
}
