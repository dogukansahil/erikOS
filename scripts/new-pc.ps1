# SPDX-License-Identifier: GPL-3.0-only
<#
Install the newest Erik OS on a brand new virtual PC, from a USB stick.

    powershell -ExecutionPolicy Bypass -File "<project>\scripts\new-pc.ps1"
    powershell -ExecutionPolicy Bypass -File "<project>\scripts\new-pc.ps1" -Edition server

What it does, like a real first installation:
  1. picks the newest ISO in releases\ (highest version number)
  2. writes it to a virtual USB stick, as you would with a real stick
     (Erik ISOs are "hybrid" images made for exactly that)
  3. builds a new PC "ErikOS-NewPC-<edition>" with an empty 40 GB disk,
     replacing the previous one (each run is a fresh machine)
  4. boots it: the empty disk has nothing, so the PC starts from the USB
     stick; after installing, "Restart now" boots the installed system
     from the internal disk by itself. Nothing else to run.
#>
param(
    [ValidateSet("desktop", "server")][string]$Edition = "desktop"
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $false
$vbm = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
$root = Split-Path -Parent $PSScriptRoot

# Run a VBoxManage call whose failure is expected and harmless.
function Try-Vbm {
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $vbm @args 2>&1 | Out-Null
    $ErrorActionPreference = $previous
}

# 1. newest release that has this edition
$iso = Get-ChildItem (Join-Path $root "releases") -Directory |
    Where-Object { $_.Name -match '^[0-9]+(\.[0-9]+)*$' } |
    Sort-Object { [version]($_.Name + $(if ($_.Name -notmatch '\.') { '.0' })) } -Descending |
    ForEach-Object { Get-Item (Join-Path $_.FullName "erikos-$($_.Name)-$Edition-amd64.iso") -ErrorAction SilentlyContinue } |
    Select-Object -First 1
if (-not $iso) { throw "No $Edition ISO found under releases\" }
$version = $iso.Directory.Name
Write-Host "Newest $Edition release: $version ($($iso.Name))"

$name = "ErikOS-NewPC-$Edition"
$dir = Join-Path $root "build-environment\virtualbox\new-pc"
$vmDir = Join-Path $dir $name
$stick = Join-Path $dir "usb-stick-$version-$Edition.vdi"
New-Item -ItemType Directory -Force $dir | Out-Null

# 3a. a new PC every run, and no old test PCs left behind (user rule,
# 2026-10-01): any earlier Erik test machine can be recreated from its ISO.
# Only test machines are removed: ISOs, the USB stick images, the WSL
# build distro and VMs that are not Erik test machines are never touched.
function Remove-TestPC([string]$vm) {
    if ((& $vbm list runningvms) -match "`"$vm`"") {
        if ($vm -ne $name) {
            Write-Host "Kept ${vm}: it is running. Close it and run this again to remove it."
            return
        }
        Try-Vbm controlvm $vm poweroff
        Start-Sleep 3
    }
    # take every DVD and stick out first, so deleting disks can never reach an ISO
    $info = & $vbm showvminfo $vm --machinereadable
    foreach ($line in $info) {
        if ($line -match '^"(SATA|IDE|USB)-(\d+)-(\d+)"="(.+\.(iso|vdi))"$' -and $Matches[4] -notmatch [regex]::Escape("\$vm\")) {
            Try-Vbm storageattach $vm --storagectl $Matches[1] --port $Matches[2] --device $Matches[3] --medium none
        }
        if ($line -match '^"(SATA|IDE)-(\d+)-(\d+)"="(.+\.iso)"$') {
            Try-Vbm storageattach $vm --storagectl $Matches[1] --port $Matches[2] --device $Matches[3] --medium emptydrive
        }
    }
    & $vbm unregistervm $vm --delete | Out-Null
    Write-Host "Removed old test PC $vm"
}
foreach ($line in (& $vbm list vms)) {
    if ($line -match '^"(ErikOS-(Try-[^"]+|Test|NewPC-[^"]+))"') { Remove-TestPC $Matches[1] }
}
# 2. the USB stick: a raw copy of the hybrid ISO, rewritten when the ISO changes
if (-not (Test-Path $stick) -or (Get-Item $stick).LastWriteTime -lt $iso.LastWriteTime) {
    if (Test-Path $stick) {
        Try-Vbm closemedium disk $stick
        Remove-Item $stick -Force
    }
    Write-Host "Writing the ISO to a virtual USB stick ..."
    & $vbm convertfromraw $iso.FullName $stick --format VDI | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not create the USB stick image" }
}

# 3b. a new PC with an empty disk
& $vbm createvm --name $name --ostype Debian_64 --basefolder $dir --register | Out-Null
$ram = if ($Edition -eq "desktop") { 6144 } else { 4096 }
# 1 vCPU and no paravirtualization: this Windows host shows RCU stalls with more.
& $vbm modifyvm $name --firmware efi --memory $ram --cpus 1 --paravirtprovider none `
    --graphicscontroller vmsvga --vram 128 --nic1 nat --audio-driver none --mouse usbtablet `
    --boot1 disk --boot2 none --boot3 none --boot4 none | Out-Null
& $vbm storagectl $name --name SATA --add sata --controller IntelAhci | Out-Null
$disk = Join-Path $vmDir "$name.vdi"
& $vbm createmedium disk --filename $disk --size 40960 --format VDI | Out-Null
& $vbm storageattach $name --storagectl SATA --port 0 --device 0 --type hdd --medium $disk | Out-Null
# The stick is a second, removable (hot-pluggable) disk: VirtualBox firmware
# cannot boot from its USB controller, and this is how firmware sees a USB
# stick anyway. The internal disk comes first, so an installed system wins.
# Immutable: every run sees the stick in its untouched state.
& $vbm storageattach $name --storagectl SATA --port 1 --device 0 --type hdd --medium $stick --mtype immutable --hotpluggable on | Out-Null

# 4. power on
& $vbm startvm $name --type gui | Out-Null
if ($LASTEXITCODE -ne 0) { throw "VirtualBox could not start $name (see the message above)." }
Write-Host ""
Write-Host "New PC '$name' is starting from the USB stick with Erik OS $version."
if ($Edition -eq "desktop") {
    Write-Host "  1. Boot menu: press Enter."
    Write-Host "  2. The installer opens by itself (press Esc once if the GNOME overview is in front)."
    Write-Host "  3. Install, keep 'Restart now' ticked, click Done: the PC restarts into the installed Erik OS."
} else {
    Write-Host "  Boot menu: choose 'Start installer' to install, or Enter for the live system."
}
