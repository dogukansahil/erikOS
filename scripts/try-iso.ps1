# SPDX-License-Identifier: GPL-3.0-only
<#
Try an Erik OS ISO in a fresh VirtualBox machine, with a window you can use.

    powershell -ExecutionPolicy Bypass -File scripts\try-iso.ps1 releases\0.3\erikos-0.3-desktop-amd64.iso

Creates "ErikOS-Try-<version>-<edition>" with an empty 40 GB disk, so the
live system and the installer always appear (a disk that already holds an
installation boots first and hides the installer). Run it again with
-Recreate to start over with an empty disk. The machine lives in
build-environment\virtualbox\try\ and never touches other VMs.

After installing: shut the installed system down, then run with -NoIso to
boot it from its disk without the ISO.
#>
param(
    [Parameter(Mandatory = $true)][string]$Iso,
    [switch]$Recreate,
    [switch]$NoIso
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $false
$vbm = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
$root = Split-Path -Parent $PSScriptRoot
# Accept paths relative to the current folder or to the project folder.
if (-not (Test-Path $Iso)) { $Iso = Join-Path $root $Iso }
$iso = (Resolve-Path $Iso).Path
if ((Split-Path $iso -Leaf) -notmatch '^erikos-([0-9.]+)-(desktop|server)-amd64\.iso$') {
    throw "Expected an ISO named erikos-<version>-<edition>-amd64.iso"
}
$version, $edition = $Matches[1], $Matches[2]
$name = "ErikOS-Try-$version-$edition"
$dir = Join-Path $root "build-environment\virtualbox\try"
$disk = Join-Path $dir "$name\$name.vdi"

$exists = (& $vbm list vms) -match "`"$name`""
$running = (& $vbm list runningvms) -match "`"$name`""
if ($running -and -not $Recreate) {
    Write-Host "$name is already running: use its VirtualBox window (find it in the taskbar or in VirtualBox Manager)."
    Write-Host "To start over with an empty disk, run this command again with -Recreate."
    exit 0
}
if ($exists -and $Recreate) {
    $ErrorActionPreference = "Continue"
    & $vbm controlvm $name poweroff 2>&1 | Out-Null
    $ErrorActionPreference = "Stop"
    Start-Sleep 2
    # take the ISO out first: only the machine's own disk is deleted
    & $vbm storageattach $name --storagectl SATA --port 1 --device 0 --type dvddrive --medium emptydrive | Out-Null
    & $vbm unregistervm $name --delete | Out-Null
    $exists = $false
}
if (-not $exists) {
    New-Item -ItemType Directory -Force $dir | Out-Null
    & $vbm createvm --name $name --ostype Debian_64 --basefolder $dir --register | Out-Null
    $ram = if ($edition -eq "desktop") { 6144 } else { 4096 }
    # 1 vCPU and no paravirtualization: this host shows RCU stalls with more.
    & $vbm modifyvm $name --firmware efi --memory $ram --cpus 1 --paravirtprovider none `
        --graphicscontroller vmsvga --vram 128 --nic1 nat --audio-driver none --mouse usbtablet | Out-Null
    & $vbm storagectl $name --name SATA --add sata --controller IntelAhci | Out-Null
    & $vbm createmedium disk --filename $disk --size 40960 --format VDI | Out-Null
    & $vbm storageattach $name --storagectl SATA --port 0 --device 0 --type hdd --medium $disk | Out-Null
    Write-Host "Created $name (empty 40 GB disk, $ram MB RAM)"
}

if ($NoIso) {
    & $vbm storageattach $name --storagectl SATA --port 1 --device 0 --type dvddrive --medium emptydrive | Out-Null
    & $vbm modifyvm $name --boot1 disk --boot2 none | Out-Null
} else {
    & $vbm storageattach $name --storagectl SATA --port 1 --device 0 --type dvddrive --medium $iso | Out-Null
    & $vbm modifyvm $name --boot1 dvd --boot2 disk | Out-Null
}
& $vbm startvm $name --type gui | Out-Null
if ($LASTEXITCODE -ne 0) { throw "VirtualBox could not start $name (see the message above)." }
Write-Host "Started $name with $(if ($NoIso) { 'its disk' } else { Split-Path $iso -Leaf })."
if (-not $NoIso) {
    Write-Host "Boot menu: press Enter. The desktop edition opens the installer by itself; press Esc once if the GNOME overview is in front of it."
}
