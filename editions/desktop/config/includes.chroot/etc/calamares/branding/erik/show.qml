/*
 * Erik OS Calamares slideshow
 * SPDX-License-Identifier: GPL-3.0-only
 */

import QtQuick 2.0;
import calamares.slideshow 1.0;

Presentation
{
    Slide {
        Image {
            source: "logo.png"
            width: 260
            height: 260
            fillMode: Image.PreserveAspectFit
            anchors.centerIn: parent
        }
    }
}
