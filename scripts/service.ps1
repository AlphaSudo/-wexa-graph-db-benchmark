[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('start', 'stop', 'evidence', 'status')]
    [string]$Action,

    [Parameter(Mandatory = $true, Position = 1)]
    [ValidateSet('neo4j', 'memgraph', 'falkordb', 'arangodb')]
    [string]$Service,

    [Parameter(Position = 2)]
    [ValidateSet('snapshot', 'preload', 'postload', 'postrun')]
    [string]$EvidencePhase = 'snapshot'
)

$ErrorActionPreference = 'Stop'
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $RepositoryRoot 'infra\compose.yaml'
$ContainerName = "wexa-$Service"
$DataDirectories = @{
    neo4j = '/data'
    memgraph = '/var/lib/memgraph'
    falkordb = '/data'
    arangodb = '/var/lib/arangodb3'
}
$StorageMount = "/var/lib/wexa-benchmark-storage/$Service"

if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
    throw 'Podman is required by this script.'
}

switch ($Action) {
    'start' {
        & (Join-Path $PSScriptRoot 'storage.ps1') status $Service
        $Running = podman ps --format '{{.Names}}'
        $Other = $Running | Where-Object { $_ -like 'wexa-*' -and $_ -ne $ContainerName }
        if ($Other) {
            throw "Stop the other benchmark service first: $($Other -join ', ')"
        }
        podman compose -f $ComposeFile --profile $Service up -d $Service
        Start-Sleep -Seconds 2
        $StartState = podman inspect $ContainerName --format '{{.State.Status}} cpus={{.HostConfig.NanoCpus}} memory={{.HostConfig.Memory}} swap={{.HostConfig.MemorySwap}}'
        Write-Output $StartState
        if ($StartState -notmatch '^running ') {
            podman logs --tail 80 $ContainerName
            throw "$Service failed to remain running"
        }
    }
    'stop' {
        podman compose -f $ComposeFile --profile $Service stop $Service
    }
    'status' {
        podman ps -a --filter "name=$ContainerName" --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
    }
    'evidence' {
        $EvidenceDirectory = Join-Path $RepositoryRoot 'results\evidence'
        New-Item -ItemType Directory -Force -Path $EvidenceDirectory | Out-Null
        $Timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
        $Destination = Join-Path $EvidenceDirectory "$Service-$EvidencePhase-$Timestamp.json"
        $LogDestination = Join-Path $EvidenceDirectory "$Service-$EvidencePhase-$Timestamp.log"
        $Inspect = (podman inspect $ContainerName | ConvertFrom-Json)[0]
        $ImageInspect = (podman image inspect $Inspect.Config.Image | ConvertFrom-Json)[0]
        $Cgroup = @{}
        $CgroupMemory = @{}
        $Filesystem = @()
        if ($Inspect.State.Status -eq 'running') {
            $CgroupLines = podman exec $ContainerName sh -lc @'
for item in memory.current memory.max memory.swap.max cpu.max pids.max; do
  if [ -f "/sys/fs/cgroup/$item" ]; then
    printf '%s=%s\n' "$item" "$(cat "/sys/fs/cgroup/$item")"
  fi
done
'@
            foreach ($Line in $CgroupLines) {
                if ($Line -match '^([^=]+)=(.*)$') {
                    $Cgroup[$Matches[1]] = $Matches[2]
                }
            }
            $MemoryLines = podman exec $ContainerName sh -lc @'
if [ -f /sys/fs/cgroup/memory.stat ]; then
  grep -E '^(anon|file|kernel|kernel_stack|pagetables|sock|shmem|slab) ' /sys/fs/cgroup/memory.stat
fi
if [ -f /sys/fs/cgroup/memory.events ]; then
  sed 's/^/event_/' /sys/fs/cgroup/memory.events
fi
'@
            foreach ($Line in $MemoryLines) {
                if ($Line -match '^([^ ]+) +(.*)$') {
                    $CgroupMemory[$Matches[1]] = $Matches[2]
                }
            }
            $DataDirectory = $DataDirectories[$Service]
            $Filesystem = @(podman exec $ContainerName sh -lc "df -B1 '$DataDirectory'")
        }
        $PublishedPorts = @(podman port $ContainerName)
        $HostStorage = @(podman machine ssh -- sudo findmnt -b -n -o TARGET,SOURCE,FSTYPE,SIZE,AVAIL,USED,OPTIONS --target $StorageMount)
        $HostStorageUsage = @(podman machine ssh -- sudo du -sb $StorageMount)
        podman logs --tail 500 $ContainerName 2>&1 | Set-Content -LiteralPath $LogDestination -Encoding utf8
        $LogSha256 = (Get-FileHash -LiteralPath $LogDestination -Algorithm SHA256).Hash.ToLowerInvariant()
        $Evidence = [ordered]@{
            schema_version = 2
            recorded_at_utc = (Get-Date).ToUniversalTime().ToString('o')
            service = $Service
            phase = $EvidencePhase
            container_name = $ContainerName
            image = $Inspect.Config.Image
            image_id = $Inspect.Image
            repo_digests = @($ImageInspect.RepoDigests)
            state = [ordered]@{
                status = $Inspect.State.Status
                oom_killed = $Inspect.State.OOMKilled
                exit_code = $Inspect.State.ExitCode
                restart_count = $Inspect.RestartCount
            }
            limits = [ordered]@{
                nano_cpus = $Inspect.HostConfig.NanoCpus
                memory_bytes = $Inspect.HostConfig.Memory
                memory_swap_bytes = $Inspect.HostConfig.MemorySwap
                pids_limit = $Inspect.HostConfig.PidsLimit
            }
            cgroup = $Cgroup
            cgroup_memory = $CgroupMemory
            published_ports = $PublishedPorts
            host_storage_mount = $HostStorage
            host_storage_usage = $HostStorageUsage
            container_filesystem = $Filesystem
            mounts = @($Inspect.Mounts | ForEach-Object {
                [ordered]@{
                    type = $_.Type
                    source = $_.Source
                    name = $_.Name
                    destination = $_.Destination
                    options = @($_.Options)
                }
            })
            startup_log = [ordered]@{
                file = (Split-Path -Leaf $LogDestination)
                sha256 = $LogSha256
                tail_lines = 500
            }
        }
        $Evidence | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Destination -Encoding utf8
        Write-Host "Saved container evidence to $Destination"
    }
}
