[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('setup', 'status', 'reset')]
    [string]$Action,

    [Parameter(Position = 1)]
    [ValidateSet('all', 'neo4j', 'memgraph', 'falkordb', 'arangodb')]
    [string]$Service = 'all'
)

$ErrorActionPreference = 'Stop'
$Services = if ($Service -eq 'all') {
    @('neo4j', 'memgraph', 'falkordb', 'arangodb')
} else {
    @($Service)
}

if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
    throw 'Podman is required.'
}

foreach ($CurrentService in $Services) {
    $RemoteRoot = '/var/lib/wexa-benchmark-storage'
    $ImagePath = "$RemoteRoot/$CurrentService.img"
    $MountPath = "$RemoteRoot/$CurrentService"
    if ($Action -eq 'reset') {
        $ContainerName = "wexa-$CurrentService"
        $Running = podman ps --filter "name=$ContainerName" --format '{{.Names}}'
        if ($Running) {
            throw "Stop $ContainerName before resetting its dedicated benchmark storage"
        }
        if (-not $ImagePath.StartsWith('/var/lib/wexa-benchmark-storage/')) {
            throw "Refusing unexpected storage image path: $ImagePath"
        }
        podman machine ssh -- sudo test -f $ImagePath
        if ($LASTEXITCODE -ne 0) {
            throw "Dedicated storage image does not exist: $ImagePath"
        }
        podman machine ssh -- sudo mountpoint -q $MountPath
        if ($LASTEXITCODE -eq 0) {
            podman machine ssh -- sudo umount $MountPath
        }
        podman machine ssh -- sudo mkfs.ext4 -F -L "wexa-$CurrentService" $ImagePath
        podman machine ssh -- sudo mount -o loop,nosuid,nodev,noexec $ImagePath $MountPath
        podman machine ssh -- sudo chown user:user $MountPath
        podman machine ssh -- sudo chmod 0777 $MountPath
        podman machine ssh -- sudo touch "$MountPath/.wexa-storage-initialized"
        if ($CurrentService -eq 'memgraph') {
            podman machine ssh -- podman unshare chown 101:103 $MountPath "$MountPath/.wexa-storage-initialized"
        }
    }
    if ($Action -eq 'setup') {
        podman machine ssh -- sudo mkdir -p $RemoteRoot $MountPath
        podman machine ssh -- sudo test -f $ImagePath
        if ($LASTEXITCODE -ne 0) {
            podman machine ssh -- sudo truncate -s 1G $ImagePath
            podman machine ssh -- sudo mkfs.ext4 -F -L "wexa-$CurrentService" $ImagePath
        }
        podman machine ssh -- sudo mountpoint -q $MountPath
        if ($LASTEXITCODE -ne 0) {
            podman machine ssh -- sudo mount -o loop,nosuid,nodev,noexec $ImagePath $MountPath
        }
        $OwnershipMarker = "$MountPath/.wexa-storage-initialized"
        podman machine ssh -- sudo test -f $OwnershipMarker
        if ($LASTEXITCODE -ne 0) {
            podman machine ssh -- sudo chown -R user:user $MountPath
            podman machine ssh -- sudo touch $OwnershipMarker
            podman machine ssh -- sudo chown user:user $OwnershipMarker
        }
        podman machine ssh -- sudo chmod 0777 $MountPath
        if ($CurrentService -eq 'memgraph') {
            # The image runs directly as uid 101/gid 103. Rootless Podman must map that
            # container identity to its subordinate host IDs before the bind mount is writable.
            podman machine ssh -- podman unshare chown 101:103 $MountPath $OwnershipMarker
        }
    }
    podman machine ssh -- sudo mountpoint -q $MountPath
    if ($LASTEXITCODE -ne 0) {
        throw "$CurrentService storage is not mounted"
    }
    podman machine ssh -- sudo findmnt -b -n -o TARGET,SOURCE,FSTYPE,SIZE,AVAIL,USED,OPTIONS --target $MountPath
}
