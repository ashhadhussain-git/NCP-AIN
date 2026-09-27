---
description: Personal study guide and lab notes for the NVIDIA-Certified Professional AI Networking exam.
---

# NCP-AIN Detailed Study Guide

Detailed personal study notes for the NVIDIA-Certified Professional: AI
Networking (NCP-AIN) exam. Use the explanations and exercises below as a
starting point, then add your own diagrams, command output, lab results, and
questions as you study.

**Interactive study site:** [Open the chapter navigation and section outline](https://ashhadhussain-git.github.io/NCP-AIN/).

> [!NOTE]
> Exam weights and objectives can change. Check the official NVIDIA resources
> before using this outline to plan your final review.

> **Reading this guide**
> Use [`SUMMARY.md`](./SUMMARY.md) as the chapter index. Each domain below is
> organized as a chapter with focused topics, practical exercises, and review
> prompts. The guide is designed for study and lab practice, not as a
> production deployment runbook.

## Table of contents

Each learning topic is organized around three questions: **What** is the
concept or component? **Why** does it matter in an AI network? **How** is it
used, verified, or troubleshot? Detailed explanations, examples, and exercises
follow these summaries.

| Chapter | Exam weight | Focus |
| --- | ---: | --- |
| [Study plan](#study-plan) | — | Six-week learning path |
| [Topology case studies and packet flows](#topology-case-studies-and-packet-flows) | — | Fabric designs and end-to-end traffic walkthroughs |
| [AI Data Center Design and Optimization](#1-ai-data-center-design-and-optimization--5) | 5% | Architecture, rails, GPU communication |
| [NVIDIA Spectrum Networking](#2-nvidia-spectrum-networking--30) | 30% | RoCE, QoS, routing, telemetry |
| [NVIDIA InfiniBand Networking](#3-nvidia-infiniband-networking--30) | 30% | Fabric management, PKeys, QoS |
| [Kubernetes Integration](#4-kubernetes-integration--5) | 5% | Operator, RDMA resources, validation |
| [Troubleshooting Tools](#5-troubleshooting-tools--20) | 20% | Diagnostic tools and workflows |
| [Automation and Configuration](#6-automation-and-configuration--10) | 10% | NVUE, Ansible, safe rollout |
| [Official resources and guided study curriculum](#official-resources) | — | Sequenced reading, learning goals, exercises, and review questions |

---

## Study plan

**What:** A six-week sequence across the exam domains, with time weighted
toward the larger networking sections.

**Why:** A schedule helps balance broad concept learning, command/lab practice,
and final review rather than leaving high-weight topics until the end.

**How:** Follow the weekly sequence below, track weak objectives, and use
timed practice in the final review period to decide what to revisit.

- [ ] Week 1: AI data center foundations
- [ ] Weeks 2–3: Spectrum networking; practice in NVIDIA Air where available
- [ ] Week 4: InfiniBand networking
- [ ] Week 5: Troubleshooting and automation
- [ ] Week 6: Kubernetes integration, review, and timed practice

Mark a week complete as you finish it. Spend extra review time on the two
30%-weight domains and revisit topics you find difficult.

## Topology case studies and packet flows

**What:** Worked examples of topology design and packet movement across
Ethernet, InfiniBand, and overlay networks.

**Why:** End-to-end flow tracing connects architecture concepts to
troubleshooting and performance reasoning.

**How:** Follow one example at a time, mark every endpoint and hop, and answer
the failure and capacity questions using evidence.

The examples below are illustrative learning scenarios, not prescriptive
production designs. Real designs depend on the selected NVIDIA platform,
software release, workload, scale, cabling, and validated deployment
documentation. The official [NVIDIA NCP-AIN exam study guide](https://dam-cdn.nvd.orangelogic.com/AssetLink/32ljugfxg1hs1sd42371npw1xmcuo1yo.pdf)
is the reference for the exam objectives; these explanations and diagrams are
original study notes to help reason through those objectives.

### Case study 1: two-tier leaf-spine AI fabric

**What:** A small, redundant fabric where server-facing leaves connect through
multiple spine paths.

**Why:** It illustrates predictable paths between server blocks and provides
a simple way to reason about capacity, oversubscription, and failures.

**How:** Trace host-to-leaf-to-spine-to-leaf links, count link capacity at
each boundary, then remove one link or switch and recalculate the available
paths and bandwidth.

Imagine four GPU servers connected to two leaf switches, with both leaves
connected to two spine switches. Each server has two network adapters, one on
each of two independent rails. The diagram is simplified: production
deployments may use many more ports, switches, rails, and failure domains.

```text
                       Spine 1       Spine 2
                        /   \         /   \
                       /     \       /     \
                  Leaf A =====         ===== Leaf B
                   /  \                       /  \
              Server 1  Server 2         Server 3  Server 4
                NIC0       NIC0             NIC0       NIC0  (rail 0)
                NIC1       NIC1             NIC1       NIC1  (rail 1)
```

Each leaf has paths through both spines to the other leaf. In a balanced
topology, equal-cost paths can share traffic; the actual distribution depends
on the routing and hashing/adaptive-routing behavior configured on the
platform. A second rail offers an additional traffic path only when the host,
adapter, cabling, switch ports, routing, and application are all wired and
configured to use it.

**Capacity exercise:** suppose each of four servers offers 2 × 200 Gb/s of
uplink capacity to the fabric. There are 1.6 Tb/s of server-facing capacity.
If the two leaves provide 4 × 200 Gb/s of aggregate spine-facing links, there
is also 1.6 Tb/s of nominal fabric-facing capacity at that boundary. This
simple equality does not guarantee 1:1 application throughput: rail placement,
oversubscription elsewhere, protocol overhead, hashing, congestion, and
failure scenarios still matter. Recalculate for one failed uplink and explain
which flows share the remaining capacity.

**Questions to answer:** Where is the first oversubscribed cut? Does traffic
between two servers attached to one leaf need to cross a spine? Which links
are shared for cross-leaf traffic? What changes if one spine or one rail is
unavailable? Which counters would confirm whether traffic is balanced?

### Case study 2: trace an Ethernet RoCEv2 GPU transfer

**What:** An RDMA data transfer between GPUs on different hosts over an
Ethernet fabric using RoCEv2.

**Why:** It connects host RDMA setup, packet encapsulation, switch forwarding,
congestion handling, and GPU-memory placement into one end-to-end flow.

**How:** Follow the numbered packet path below, then correlate endpoint
completion with switch queue, ECN/PFC, drop, and link counters.

Trace a message from a GPU on Server 1 to a GPU on Server 3 in the topology
above:

1. The application and GPU communication library prepare an RDMA operation
   and buffers. With a supported GPUDirect RDMA path, the adapter can transfer
   payload to or from GPU memory without a CPU staging copy; setup and
   completion still involve software.
2. The host RDMA stack posts work to a queue pair. The NIC/SuperNIC constructs
   RoCEv2 traffic, carried over UDP/IP inside Ethernet. The source adapter
   chooses the relevant local port/rail and emits packets.
3. The first switch classifies the packet according to the configured traffic
   markings and maps it to a queue/priority. Switches forward using the
   underlay Ethernet/IP information. Correct MTU, addressing, routing, and
   consistent QoS mapping along the path are required.
4. If queues build, ECN can mark congestion for an endpoint response. PFC may
   pause a configured priority on a specific congested link where the fabric
   design uses it. Neither mechanism repairs a bad route, an oversubscribed
   topology, or a slow endpoint.
5. Routing forwards the packet over an available path through a spine and the
   destination leaf. Equal-cost or adaptive path behavior depends on the
   switch platform and configuration.
6. The destination NIC validates and processes the RDMA traffic and places
   data into the registered destination memory region, potentially GPU memory
   on a supported GPUDirect path. The RDMA completion and application-level
   synchronization determine when the receiving GPU can consume the data.

```text
GPU 1 -> RDMA library/queue pair -> NIC 1
      -> Leaf A -> Spine -> Leaf B -> NIC 3
      -> destination memory/GPU 3 -> completion -> application
```

Keep the **control plane** distinct from this packet path: routing and fabric
protocols establish state used to forward traffic, while individual data
packets traverse the resulting forwarding path. For a slow transfer, compare
host queue/counter data, per-port and per-queue switch utilization, ECN/PFC
counters, drops, latency, and application progress in a common time window.

### Case study 3: trace an InfiniBand RDMA operation

**What:** An RDMA operation between InfiniBand endpoints, including host
queue-pair setup and fabric forwarding.

**Why:** It separates subnet management from the data path and shows how
addressing, partition membership, and link state affect communication.

**How:** Trace source QP/HCA to destination HCA/CQ; check SM discovery, path,
PKey membership, and physical links when the operation fails.

Use the same two-server scenario, but attach the endpoints to an InfiniBand
fabric. Before testing, verify active links, discovered HCAs/switches, a
functioning Subnet Manager, expected addressing/path state, and compatible
partition membership.

```text
GPU/application -> RDMA verbs + queue pair -> source HCA
                -> IB switch path (LID/VL/PKey state)
                -> destination HCA -> registered memory/GPU
                -> completion queue -> application

SM control/management: discovers and configures the fabric; it is not
                       an extra per-packet hop in the data path.
```

The application posts work to the RDMA stack; the source HCA transmits over
the selected physical port. Fabric forwarding follows the configured
InfiniBand path. PKeys govern whether endpoints are permitted to exchange
traffic in the relevant partition, while QoS/service-level and virtual-lane
configuration affect traffic treatment. The destination HCA handles the
operation and reports completion to the host. Exact path selection and
features depend on the fabric and adapter configuration.

If the operation fails, first distinguish link/discovery problems from
partition/path problems and from performance issues. Check the source and
destination HCA state, SM and fabric visibility, PKey membership, link errors,
and then run a controlled reachability or performance test. A successful
reachability probe does not establish expected bandwidth or application
performance.

### Case study 4: EVPN/VXLAN tenant packet flow

**What:** A tenant Ethernet frame encapsulated by one VTEP, routed across an
IP underlay, then decapsulated by a remote VTEP.

**Why:** It demonstrates how shared physical switching can provide isolated
logical networks and why overlay and underlay faults must be distinguished.

**How:** Trace the inner frame and outer packet separately; validate tenant
VNI mapping, EVPN reachability, and VTEP-to-VTEP underlay connectivity.

Consider two hosts in the same tenant attached to different Ethernet leaves.
Each leaf acts as a VTEP, and both endpoints belong to the same configured
overlay segment/VNI. The routed underlay provides reachability between VTEP
addresses; BGP EVPN distributes overlay endpoint reachability.

```text
Host A -- Leaf/VTEP A == routed IP underlay == Leaf/VTEP B -- Host B
          |<------ same tenant overlay/VNI ------>|

Inner frame:       Host A -> Host B (tenant traffic)
Outer packet:      VTEP A -> VTEP B (underlay transport)
Control plane:     BGP EVPN advertises overlay reachability
```

For a known remote endpoint, VTEP A encapsulates the tenant frame in an outer
packet addressed to VTEP B. The underlay routes that outer packet, potentially
across multiple equal-cost paths. VTEP B decapsulates it and forwards the
original frame toward Host B. The underlay does not need to learn every
tenant's inner MAC as a directly attached endpoint; the overlay control plane
and VTEPs provide that mapping.

If Host A cannot reach Host B, check in layers: local host attachment and
VLAN/VNI mapping; BGP EVPN neighbor and route state; remote endpoint
reachability; VTEP IP reachability in the underlay; and physical links,
queues, and drops. For isolation failures, verify that tenants map to the
intended distinct VNIs and that route import/export policy is correct.

### Packet and traffic-flow review checklist

**What:** A repeatable worksheet for describing a packet's endpoints,
encapsulation, forwarding state, path, policy, congestion, and completion.

**Why:** A layer-by-layer trace prevents confusing a control-plane issue with
a data-path, endpoint, or application issue.

**How:** Fill in each item below for one real or hypothetical flow and cite
the counter, log, or test that supports each conclusion.

For any flow scenario, sketch or write down:

1. **Endpoints:** source/destination workload, GPU, host, and adapter.
2. **Encapsulation:** protocol in use (for example, RoCEv2 over UDP/IP or an
   InfiniBand transport); for overlays, record both inner and outer headers.
3. **Forwarding state:** what control-plane state and addresses each hop uses.
4. **Policy:** VLAN/VNI or PKey membership, QoS class, and applicable ACLs.
5. **Path:** each port/switch, equal-cost path, rail, and shared bottleneck.
6. **Congestion:** queue buildup, ECN marks, PFC pauses where applicable,
   drops, and endpoint response.
7. **Completion:** destination memory placement, transport completion, and
   application consumption/synchronization.
8. **Evidence:** exact counters, logs, timestamps, and tests that prove or
   disprove each hypothesis.

For collective traffic, repeat the trace for all participating ranks. Many
flows can synchronize into bursts; the busiest link or slowest participant
can determine collective completion time even if average fabric utilization
appears moderate.

## 1. AI Data Center Design and Optimization — 5%

**What:** The architecture and communication patterns of GPU-based AI
infrastructure.

**Why:** Network capacity and topology affect accelerator utilization and
distributed job completion.

**How:** Identify system components, map scale-up/scale-out paths, and reason
about rails, collectives, and communication overhead.

### 1.1 Describe an AI factory networking architecture and its components

**What:** The coordinated compute, scale-up, scale-out, storage, and
management components that deliver AI training and inference.

**Why:** Network or service bottlenecks can leave GPUs idle and reduce job
throughput even when accelerator capacity is available.

**How:** Diagram each component and traffic plane, mark their connections and
boundaries, and explain the role and failure impact of every component.

An AI factory is designed to turn data into trained or served models. Its
compute, storage, power, cooling, and network capacity must be planned as one
system. Large GPU jobs create many synchronized flows; a slow or oversubscribed
network can leave expensive accelerators waiting instead of computing.

Think of the architecture as several cooperating planes rather than one
undifferentiated network:

| Component | Role in the AI factory | Networking perspective |
| --- | --- | --- |
| GPU and compute node | Execute model training or inference; nodes may contain multiple GPUs | Exchanges data within the node and with remote nodes; GPU count alone does not determine network bandwidth |
| NVLink and NVSwitch | Connect GPUs within supported systems | Provide high-bandwidth scale-up communication; distinct from the data-center scale-out fabric |
| NIC / SuperNIC | Connect a host to an Ethernet network and support data movement | Provides host-facing ports and, depending on platform, RDMA and hardware offloads |
| NVIDIA BlueField DPU | Programmable data-processing unit with Arm compute and networking interfaces | Can accelerate or isolate infrastructure services such as networking, security, and storage; exact functions depend on the BlueField generation and deployed software |
| Leaf switches | Attach servers and provide access into the fabric | Aggregate host links and connect to spine or higher-tier switches |
| Spine switches | Interconnect leaf blocks in a scalable fabric | Provide paths between leaves; count, port speed, and topology determine available aggregate capacity |
| Scalable unit (SU) | Repeatable building block used to grow an AI factory | Treat its exact contents and scale as design-specific; identify its compute, switch, cabling, and inter-unit boundaries from the reference architecture |
| Storage network | Connects compute to training datasets, checkpoints, and other storage services | Capacity and path design affect data loading and checkpoint traffic; may share or use separate infrastructure depending on the architecture |
| Management / service network | Supports provisioning, monitoring, and operations | Carries control and operational traffic and should be understood separately from GPU payload traffic |

The **scale-up domain** connects components within a server or tightly coupled
system, commonly using GPU interconnects. The **scale-out domain** connects
servers across the data-center fabric using Ethernet/RoCE or InfiniBand.
Storage and management traffic have their own requirements. One physical
infrastructure may carry more than one traffic type, but sharing it does not
make the traffic's performance and isolation needs identical.

### Scalable units and leaf-spine design

**What:** A scalable unit is a repeatable design building block; leaf-spine
is a multi-path fabric connecting endpoint-facing leaves through spines.

**Why:** Repeatable units simplify growth, while topology and link ratios
determine path diversity, aggregate bandwidth, and potential bottlenecks.

**How:** Identify what a reference design repeats, draw a leaf-spine path,
and calculate offered downlink capacity versus uplink capacity.

A scalable unit (SU) is a repeatable building block in a given reference
architecture. Replicating a validated unit can simplify capacity planning,
cabling, deployment, and fault isolation. Do not assume every design uses the
same SU definition: identify which compute, network, storage, and service
components it contains, and which links connect it to other units.

In a basic leaf-spine fabric, each host attaches to a leaf, and each leaf
connects to every spine. Paths between hosts in different leaf blocks usually
have a predictable number of switch hops. Multiple equal-cost paths can provide
aggregate capacity and resilience, provided routing and link utilization are
working as intended.

```text
Compute / GPU nodes              Fabric
  Node A ---- Leaf A ===== Spine 1 ===== Leaf B ---- Node C
  Node B ----   |   ===== Spine 2 =====   |   ---- Node D
                |                          |
            local hosts                 local hosts

The double lines represent multiple links in a simplified drawing.
Actual link count, speed, and topology are design-specific.
```

Draw a small topology and trace traffic between two hosts on one leaf and on
different leaves. Identify the links shared by many flows. Calculate a simple
oversubscription ratio as total offered downlink bandwidth divided by total
uplink bandwidth; a ratio above 1 means not all host ports can run at line rate
simultaneously toward the rest of the fabric.

### 1.2 Describe rail-optimized topologies for high-performance AI workloads

**What:** A topology that aligns corresponding GPU/NIC positions across
servers into parallel network rails.

**Why:** Independent rails can distribute collective traffic and reduce
contention, provided they remain balanced and sufficiently independent.

**How:** Map GPU-to-NIC-to-switch-to-uplink for every rail, then trace
collectives and evaluate one-link and one-rail failures.

In a rail-optimized GPU cluster, network paths are organized into parallel
rails and GPU/NIC positions are connected consistently across servers. For
example, traffic associated with GPU/NIC position 0 can use rail 0 across
nodes, while position 1 uses rail 1. This can give distributed GPU collectives
multiple parallel paths and limit competition between traffic assigned to
different rails.

```text
                Rail 0                         Rail 1
Node A: GPU 0 -> NIC 0 -> Leaf A0       GPU 1 -> NIC 1 -> Leaf A1
Node B: GPU 0 -> NIC 0 -> Leaf B0       GPU 1 -> NIC 1 -> Leaf B1
                         \  spine paths  /                \ spine paths /

Illustrative only: real GPU/NIC counts and rail-to-switch mappings vary.
```

Rails provide useful parallelism only when the end-to-end mapping is correct:
GPU-to-NIC affinity, adapter ports, switch connectivity, routing, and
application/library behavior must agree. Map each GPU to its local NIC, switch
port, leaf, and uplink. Then trace a collective across multiple nodes. If one
rail is unavailable, determine whether traffic fails over, loses capacity, or
becomes imbalanced; do not assume automatic failover or linear bandwidth
scaling. Cabling, routing, congestion, and shared uplinks can still become
bottlenecks.

Rail switches are the first switching tier for GPU-facing network links in many rail-optimized designs. A rail groups corresponding endpoint links across servers so their traffic can use a consistent parallel path into the fabric. Some designs use a separate switch per rail; others integrate rail behavior into a leaf layer. Follow the reference topology and map each GPU/NIC port to its switch, uplink, and inter-unit path. A rail alone does not guarantee non-blocking bandwidth, tenant isolation, or automatic failover; those depend on capacity, topology, routing, and configuration.

### 1.3 Describe GPU-to-GPU communications

**What:** Data movement between GPUs, either within a node over supported
GPU interconnects or between nodes over an RDMA-capable network.

**Why:** Distributed training depends on communication patterns such as
all-reduce and all-to-all; a slow rank or congested path can delay all
participants.

**How:** Trace the complete path from source GPU through software, adapter,
fabric, and destination GPU; account for topology, message pattern, completion,
and synchronization.

GPU-to-GPU communication can stay within one node or cross the scale-out
network. The communication library/runtime and topology determine which
available paths are used; an application-level “GPU-to-GPU” operation is not
necessarily a single direct physical link.

| Communication scope | Typical path | What to understand |
| --- | --- | --- |
| Within a node | GPU ↔ NVLink/NVSwitch ↔ GPU, where supported | Link topology and bandwidth differ by platform; identify local GPU connectivity and its failure/monitoring domain |
| Across nodes | GPU ↔ host communication stack / RDMA ↔ NIC ↔ Ethernet/RoCE or InfiniBand fabric ↔ remote NIC ↔ GPU | The complete path includes host software, adapter, network topology, congestion behavior, and destination placement |
| To/from storage | GPU/node ↔ host and storage software ↔ storage network/service | Data staging, storage throughput, and checkpointing can compete with or be separate from GPU collective traffic |

Collective communication patterns explain why AI workloads can stress a
network differently from independent request/response flows:

- **All-reduce:** ranks contribute values and receive a reduced result.
  Training frameworks commonly use it to aggregate gradients. The algorithm
  may form rings, trees, or other schedules; each has different traffic and
  sensitivity to topology.
- **All-gather / reduce-scatter:** move or reduce different portions of data
  across ranks and are often combined to implement larger collectives.
- **All-to-all:** each rank exchanges data with many or all other ranks. It can
  create many simultaneous flows and expose oversubscription or path imbalance.

For an inter-node transfer, trace the sending GPU, communication library,
RDMA operation and buffers, local NIC, fabric path, remote NIC, destination
memory/GPU, and completion/synchronization. With supported GPUDirect RDMA,
payload can move between adapter and GPU memory without a CPU staging copy;
the supported hardware/software stack and correct configuration are required.
RDMA reduces CPU data-path work but still requires setup, permissions, and
software coordination.

Collectives often synchronize participants. A slow rank, congested rail, or
imbalanced path may delay completion for the whole operation. Thus, aggregate
link speed alone is not a performance guarantee: consider topology, number of
active flows, message size, congestion, endpoint behavior, and application
overlap.

### RDMA and GPUDirect concepts

**What:** RDMA accesses registered remote memory with reduced CPU data-path
involvement; GPUDirect RDMA can enable supported NIC-to-GPU-memory transfers.

**Why:** These mechanisms can reduce copies and CPU overhead for large-scale
GPU communication, but only on compatible, correctly configured systems.

**How:** Verify hardware/software support, memory registration and permissions,
adapter configuration, and that the workload actually uses the intended
transfer path.

Remote Direct Memory Access (RDMA) lets a registered memory region on one host
be accessed by a remote peer with less CPU involvement than a conventional
socket-copy data path. RDMA does not mean “no software”: memory registration,
queue setup, permissions, addressing, and reliable transport behavior still
matter.

GPUDirect RDMA enables supported adapters to transfer data to or from GPU memory
without routing every payload through a CPU-owned staging buffer. Confirm
compatibility across GPU, driver, adapter, firmware, and software versions;
then validate that the workload is actually using the intended data path.
Remember that Ethernet RoCE needs a correctly engineered congestion and loss
strategy, while InfiniBand uses its own link and fabric mechanisms.

**Review questions:** Which components are intra-node vs. inter-node? What
creates oversubscription? Trace one GPU-to-GPU transfer across hosts. Why can
RDMA improve CPU efficiency without eliminating configuration requirements?

## 2. NVIDIA Spectrum Networking — 30%

**What:** Ethernet networking concepts and NVIDIA platform capabilities used
to connect AI workloads, including RoCE, QoS, routing, and operations.

**Why:** This high-weight domain tests how to configure, validate, and diagnose
AI traffic across an Ethernet fabric.

**How:** Trace the host-to-host path, validate configuration end to end, and
correlate host and switch telemetry under representative load.

### 2.1 Configure NVIDIA Spectrum-X switches for RoCE

**What:** RoCE carries RDMA traffic over Ethernet; Spectrum-X is NVIDIA's
Ethernet platform for AI networking.

**Why:** The endpoint RDMA stack and Ethernet fabric must work together for
reachability, congestion handling, and predictable performance.

**How:** Validate the host adapter/driver, addressing, routes, MTU, QoS, and
congestion behavior end to end; test performance beyond basic IP reachability.

RoCE (RDMA over Converged Ethernet) carries RDMA traffic over Ethernet. RoCEv2
uses IP/UDP encapsulation, so normal Ethernet/IP reachability and the RDMA
configuration both matter. A successful ping is not proof that RDMA is
configured, and a working RDMA session is not proof that the fabric is
performing well under load.

Study the entire path: host adapter and driver, addressing and routing,
switching, MTU consistency, traffic classification, congestion control, and
the application’s RDMA settings. Establish a baseline with a single pair of
hosts before adding scale or multiple traffic classes. Check product and
software-version documentation for exact commands and supported features;
switch syntax and defaults can vary.

Spectrum-X is NVIDIA's Ethernet platform for AI workloads. Learn the roles of
switches, adapters, and software as an end-to-end system rather than assuming
that one switch feature alone guarantees performance. Be ready to diagnose
asymmetric paths, mismatched MTUs, incorrect priorities, and congestion points.

#### RoCE bring-up and validation workflow

**What:** A staged process validates the switch, host adapter, and Ethernet/RDMA configuration as one end-to-end path.

**Why:** RoCE depends on compatible endpoint and fabric behavior; IP reachability alone does not establish RDMA operation or performance.

**How:** Confirm platform, firmware, driver, and software compatibility; verify physical links, addressing, routes, and end-to-end MTU; check host RDMA device and traffic-class settings; align switch QoS and congestion configuration; test one host pair before adding concurrent flows; record counters and a rollback plan before scaling changes. Use release-specific NVIDIA documentation for commands and supported features.

#### Benchmarking with CloudAI Benchmark

**What:** CloudAI Benchmark measures AI networking behavior under defined, supported test conditions.

**Why:** Link counters and basic point-to-point checks do not necessarily predict performance for an application's communication pattern or a multi-node workload.

**How:** Record topology, versions, workload, scale, and baseline; run supported tests and correlate throughput and latency with endpoint and switch telemetry. Compare like-for-like runs after changing one variable. Follow current documentation; a score alone is not a root-cause diagnosis.

### 2.2 Enable and verify QoS, ECN, PFC, and advanced features

**What:** QoS classifies traffic, ECN marks congestion for endpoint reaction,
and PFC pauses a selected priority on a link.

**Why:** Consistent traffic treatment and carefully designed congestion
response help protect latency-sensitive and RDMA flows under load.

**How:** Inspect classification, queue mapping, ECN marks, PFC pause counters,
drops, and endpoint response together; do not use PFC as a substitute for
congestion control.

Quality of Service (QoS) classifies traffic and maps it to queues or priorities.
The mapping must be consistent across hosts and switches; otherwise traffic can
enter the fabric in an unexpected class. Preserve capacity for control and
management traffic so bulk data does not starve essential protocols.

Explicit Congestion Notification (ECN) allows a congested queue to mark packets
before it drops them. A capable receiver/adapter can react by reducing its
sending rate. Priority Flow Control (PFC) pauses a selected priority on a link
when buffers approach a threshold. PFC can limit loss locally, but poorly
designed pause propagation can cause head-of-line blocking or congestion
spreading. It is not a substitute for congestion control or correct buffer and
queue design.

Learn the intended sequence: classify the flow, observe queue buildup, signal
congestion with ECN, and use PFC only as a carefully engineered safeguard where
the design requires it. Validate priority-to-queue mappings, ECN thresholds,
PFC counters, pause duration, drops, and end-host reaction together. Never copy
thresholds from another deployment without checking platform guidance and
traffic characteristics.

#### Adaptive routing and telemetry

**What:** Adaptive routing can select among paths using fabric conditions;
telemetry exposes utilization, congestion, latency, and events.

**Why:** Static path hashing may imbalance synchronized AI flows, while
telemetry helps distinguish fabric congestion from endpoint or application
delays.

**How:** Compare per-path and per-queue measurements on synchronized
timestamps and confirm actual path selection and platform feature support.

Equal-cost multipath (ECMP) commonly selects a path using flow attributes.
Several large synchronized flows can hash onto the same path while other paths
remain underused. Adaptive routing can select among available paths based on
current conditions, but actual behavior depends on platform support, topology,
configuration, and flow type.

Telemetry makes the behavior observable. Compare per-link and per-queue
utilization, congestion marks, drops, latency, and retransmission or recovery
indicators over the same time window. Distinguish a congested link from a
slow endpoint or an application waiting on synchronization. Learn how the
chosen NVIDIA monitoring tools collect and display fabric state, and verify
sampling intervals and time synchronization before correlating events.

### 2.3 Configure multi-tenancy with BGP EVPN

**What:** EVPN distributes overlay reachability using BGP; VTEPs encapsulate
and decapsulate VXLAN; VNIs identify overlay segments.

**Why:** Together they enable tenant segmentation over a routed, shared
underlay and provide control-plane endpoint learning.

**How:** Verify underlay VTEP reachability, BGP EVPN routes and policy, VNI
mapping, and host attachment; trace both inner and outer packet headers.

VXLAN encapsulates an overlay Ethernet frame inside an IP/UDP packet to carry
Layer 2 segments across a routed underlay. A VXLAN Tunnel Endpoint (VTEP)
encapsulates and decapsulates that traffic. A VXLAN Network Identifier (VNI)
identifies an overlay segment. EVPN uses BGP to distribute reachability
information so VTEPs can learn which remote endpoint is reachable through
which tunnel.

Keep the underlay and overlay separate in your mental model. The underlay must
provide IP reachability between VTEP addresses; the overlay provides tenant
connectivity. Trace a packet from a host through its local VTEP, across the
underlay, and to the remote VTEP. Know where MAC/IP learning occurs, how a
VNI maps to a tenant segment, and why route-target/import policy and correct
addressing matter. For L3 services, study the applicable EVPN model and its
control-plane routes from official documentation.

**Practice:** draw two tenants on shared switches, each with isolated VNIs.
Explain how you would check VTEP reachability, BGP session state, route
advertisement, VNI mapping, and host attachment when one tenant cannot reach a
remote host.

### 2.4 Use NVIDIA Air to simulate network environments

**What:** A network simulation environment for supported NVIDIA networking
topologies and configurations.

**Why:** Simulation allows safe practice and configuration validation before
changes are attempted on physical infrastructure.

**How:** Build a supported lab, record topology and assumptions, test normal
and failure cases, and separately validate physical behavior on real hardware.

NVIDIA Air is a network simulation environment useful for learning and
validating supported topologies and configurations without first changing a
production fabric. Treat simulation results as evidence for the simulated
features only: it cannot prove physical cabling, optics, actual hardware
capacity, or behavior of features not represented by the environment.

Use a lab to practice configuration changes, expected state, and failure
scenarios. Save the topology, assumptions, commands, and before/after output
with your notes. Confirm current access and feature availability in NVIDIA's
documentation.

### 2.5 Diagnose congestion or packet loss with in-band telemetry and WJH

**What:** WJH helps investigate switch-level packet events; NetQ provides
broader fabric operations and health visibility, depending on deployment.

**Why:** One narrows a specific event while the other helps determine whether
the condition spans devices or the wider fabric.

**How:** Correlate timestamps, device/port/queue context, counters, and host
symptoms; use both as evidence rather than assuming either alone is root cause.

What Just Happened (WJH) helps investigate switch events such as packet drops
and their reported causes. Use it to narrow a specific event to a port, reason,
or relevant hardware context, then correlate its timestamp and counters with
the host and other switches. A reported drop reason is a clue to validate, not
by itself a complete end-to-end root cause.

In-band telemetry, where supported and enabled, can expose path and queue observations for selected traffic. Correlate those records with WJH, switch counters, and host symptoms; check timestamps, sampling interval, and telemetry scope.

### 2.6 Use NetQ for real-time network monitoring

**What:** NVIDIA NetQ provides fabric-wide operational visibility, including topology, health, and supported congestion or latency measurements depending on deployment and release.

**Why:** Fabric context helps determine whether a problem is isolated to a device or link, follows a path, or spans the wider network.

**How:** Confirm devices report to NetQ, inspect topology and health, then compare time-aligned latency, congestion, link, and event data for the affected path. Correlate findings with switch, WJH, telemetry, host RDMA, and workload evidence. Metrics vary by version; a dashboard alone does not prove root cause.

NetQ provides broader fabric operations and visibility, including topology and
health information depending on the deployed version and configuration. Use
it to identify whether an issue is isolated or spans multiple devices, and to
compare configuration or operational state across the fabric. Know when to
use event-level switch evidence (WJH) versus fabric-wide context (NetQ); neither
replaces checking endpoint drivers, application symptoms, and physical links.

### 2.7 Install NVIDIA DOCA

**What:** DOCA is NVIDIA's software development framework for supported
networking platforms; SuperNICs are high-performance adapters for demanding
network workloads.

**Why:** Software frameworks and adapter offloads affect how data-plane,
RDMA, congestion, and telemetry functions are implemented.

**How:** Identify the host/DPU component and product generation, verify
version compatibility, and inspect supported offloads and operational state
using current product documentation.

**DOCA installation workflow:** Identify the BlueField generation, operating mode, host OS, firmware, and required services. Select a supported DOCA release and follow its host- or DPU-side installation guide, including prerequisites and any documented reboot or firmware steps. Verify the installed version, device and driver state, required services, and the specific application or offload. Do not mix packages from incompatible releases or assume that installation enables every feature.

DOCA is NVIDIA's software development framework for supported DPUs and
networking platforms. It includes APIs, libraries, and tools; it is not a
single switch command or a synonym for all networking software. Understand
which host or DPU component runs a given service and which device/driver
versions it requires.

### 2.8 Configure NVIDIA SuperNIC functionality

**What:** NVIDIA SuperNICs provide high-performance host networking and, depending on product and software support, accelerated packet processing, RDMA, congestion management, and telemetry.

**Why:** Adapter offloads can improve data-path efficiency and cooperate with the Ethernet fabric to manage AI traffic at scale.

**How:** Verify adapter model, firmware, driver, link and RDMA state, then validate only the packet-processing and congestion features documented for that product and release. Compare a controlled baseline under representative load using adapter counters, switch queues, ECN/PFC statistics, and workload measurements.

SuperNIC refers to high-performance adapters designed for demanding
accelerated-computing network workloads. Depending on product and deployment,
hardware and software can support packet processing, RDMA, congestion
management, and telemetry. Learn the role of the adapter in the end-to-end
data path and how to check link state, firmware/driver compatibility, and
relevant offload configuration from current product documentation.

**Review questions:** Why is ping insufficient to verify RoCE? How do ECN and
PFC differ? What does each of VTEP, VNI, and EVPN do? Which tool would you use
first for a single switch drop versus a fabric-wide health question?

## 3. NVIDIA InfiniBand Networking — 30%

**What:** InfiniBand fabric components and behavior, from subnet management
and endpoint RDMA to partitioning, QoS, and monitoring.

**Why:** This high-weight domain requires distinguishing fabric control,
permissions, physical health, and data-path performance.

**How:** Trace a QP operation across the fabric and validate SM state, HCA
ports, PKeys, paths, and counters in layers.

### Fabric bring-up and Subnet Manager high availability

**What:** Fabric initialization discovers endpoints and switches and uses a
Subnet Manager (SM) to configure subnet state; high availability provides
standby management capability.

**Why:** InfiniBand depends on valid fabric discovery and path configuration,
and an unavailable SM can prevent required management changes or recovery.

**How:** Verify cabling and active links first, then SM master/standby state,
discovered devices, addressing/path state, and controlled failover behavior.

InfiniBand relies on a Subnet Manager (SM) to discover the fabric, assign
identifiers and paths, and configure switches and endpoints. Before diagnosing
software state, verify the physical layer: correct port-to-port cabling, link
state, supported speed/width, and error counters. A link light alone does not
prove that the port is active and configured in the fabric.

During bring-up, confirm that the intended SM is active, that switches and
host channel adapters (HCAs) are discovered, and that addressing and routing
state are consistent. High availability typically uses a master SM with one
or more standby candidates; the exact election and failover behavior depends
on the SM implementation and configuration. Test failover in a controlled
environment and verify the resulting fabric state rather than assuming that a
standby is ready merely because its process is running.

### InfiniBand packet anatomy and end-to-end flow

**What:** The RDMA operation path from application work request and QP, through
the source HCA and fabric, to destination memory and completion queue.

**Why:** It separates application setup, host transport, fabric forwarding,
partition policy, and physical-link behavior for diagnosis.

**How:** Trace endpoints, addressing, QP/transport, PKey, service
level/virtual lane, switch path, destination operation, and completion. Keep
SM configuration separate from per-packet forwarding.

Separate the **control/management plane** from the **data path**. The Subnet
Manager discovers the subnet and configures information such as identifiers
and forwarding paths. Once the fabric is configured, the SM is not an
additional switch hop for every application packet.

An RDMA application typically uses the verbs interface to create a protection
domain, register memory, create a queue pair (QP), and post work requests.
Memory registration establishes the permissions and keys used for remote
access. A completion queue (CQ) reports completion events to the application.
The exact setup and transport behavior depends on the application and selected
InfiniBand transport.

```text
Application
  -> verbs work request on a QP
  -> source HCA reads registered source buffer
  -> packet traverses links and switches on the configured path
  -> destination HCA validates and performs the requested operation
  -> destination memory is updated
  -> completion is placed on a CQ and consumed by the application
```

For a simplified packet walk, the source HCA forms transport and network
headers for the operation. The destination QP and packet sequence information
help the destination transport endpoint identify and process the traffic.
Switches forward within a subnet using the configured InfiniBand path and
addressing; a routed multi-subnet design can involve additional global
address/routing information. Do not assume every fabric uses the same
addressing or routing mode.

At each physical link, InfiniBand uses credit-based flow control: a sender
must have available receive-buffer credits before transmitting on that
virtual lane. QoS service levels can map traffic to virtual lanes, allowing
classes of traffic to be treated separately. Credits protect the local link
from overrunning the receiver's buffers; they do not prove that the end-to-end
path is uncongested or that an application has enough bandwidth.

PKeys also participate in communication permission checks. A healthy physical
link and a valid route are not sufficient if endpoint partition membership
does not permit the exchange. Trace both endpoints' PKey configuration and
membership when only a subset of peers can communicate.

**Walkthrough exercise:** select two endpoints and draw every HCA, switch,
link, and (if present) router between them. Record the source and destination
identifiers, relevant QP/transport, PKey, service level/virtual lane, and
expected forwarding path from your lab documentation. Then predict what you
would observe if (1) a link is down, (2) a PKey is mismatched, (3) a receive
buffer has no credits, or (4) the RDMA operation completes but the application
does not make progress.

**Diagnosis order:** confirm local HCA/port state; confirm fabric discovery
and SM/path configuration; verify endpoint addressing and PKey membership;
inspect link errors and VL/credit-related counters supported by the platform;
then run a controlled reachability and RDMA performance test. Use
`iblinkinfo`, `ibdiagnet`, UFM, and host-side tools as appropriate, and compare
timestamps rather than inferring a cause from a single counter.

### Partition keys (PKeys)

**What:** PKeys identify InfiniBand partition membership and constrain which
ports may communicate under the configured membership rules.

**Why:** Correct routing and link state cannot make a communication succeed
when endpoint partition membership does not permit it.

**How:** Compare PKey values and full/limited membership on both endpoints
and verify the active fabric configuration before changing routes.

PKeys provide partition-based access control for InfiniBand communication.
Ports use PKey membership to determine which partition traffic they may
exchange. Full and limited membership are different: in general, full members
can communicate with other permitted members more broadly, while limited
members have more restricted communication rights. Check the exact PKey rules
and operational behavior in the relevant InfiniBand/NVIDIA documentation.

Think of PKeys as a fabric-level isolation mechanism, not as a drop-in synonym
for Ethernet VLANs. Verify the PKey assigned to each relevant port and the
configured membership on both communicating endpoints. When communication
fails only for some nodes, compare membership and partition configuration
before changing routing.

### QoS, virtual lanes, and adaptive routing

**What:** InfiniBand QoS maps service levels to virtual lanes; adaptive routing
selects among available paths based on supported fabric behavior.

**Why:** Traffic classes may need separation, and alternate paths can help
avoid congestion when the topology and configuration support them.

**How:** Inspect effective SL-to-VL mapping, switch/SM capabilities, route
state, and per-link evidence; verify there is a usable alternate path.

InfiniBand QoS uses service levels and virtual lanes (VLs) to map traffic into
separate link-level queues. VLs can help isolate traffic classes and avoid one
blocked class holding up unrelated traffic, subject to correct configuration
and available resources. Learn how service levels map to VLs in the deployed
fabric and how to inspect the effective state.

Adaptive routing can select paths based on fabric conditions rather than
always relying on one static route choice. Understand that the SM and switch
capabilities/configuration influence available paths. It cannot route around
every failure if the topology has no alternate path; confirm topology,
supported features, and route state.

### Unified Fabric Manager (UFM)

**What:** UFM is a fabric-management solution for supported InfiniBand
deployments, with topology, health, and operational views.

**Why:** It helps establish whether an incident is local or fabric-wide and
where to focus physical or host-side investigation.

**How:** Scope the event in UFM, inspect affected devices/links and counters,
then corroborate with HCA state and targeted diagnostics at matching timestamps.

UFM is NVIDIA's fabric management and monitoring solution for supported
InfiniBand environments. Use it to view topology and device/link status,
monitor performance and health, and help locate problematic links or devices.
Know the difference between a visualization/alert and the underlying counters
or state that support a diagnosis.

For a fabric incident, record the scope, affected endpoints, time window, link
state, error counters, and recent changes. Compare UFM's view with host-side
HCA information and targeted fabric diagnostics. Familiarize yourself with
the available UFM features in the version used in your lab.

**Review questions:** What fabric state does the SM establish? What is the
difference between PKey membership levels? How do VLs relate to QoS? What
evidence would you collect before replacing a cable or changing a partition?

## 4. Kubernetes Integration — 5%

**What:** Kubernetes-managed NVIDIA networking components and the resources
that make network devices available to workloads.

**Why:** Distributed GPU workloads need the correct devices and network paths
inside scheduled pods, not only healthy cluster services.

**How:** Follow operator reconciliation from host prerequisites to node
resources, pod interfaces, and an end-to-end communication test.

### NVIDIA Network Operator

**What:** A Kubernetes operator that manages selected NVIDIA networking
components on supported clusters.

**Why:** It coordinates deployment and reconciliation of networking software
and resources across nodes, reducing manual per-node setup.

**How:** Follow the compatibility matrix and versioned install guide, configure
the required components, then verify reconciliation, pods, node state, and
events.

The NVIDIA Network Operator manages networking components in Kubernetes
clusters that use supported NVIDIA adapters and software. Depending on the
version and selected components, it can help deploy drivers, device plugins,
RDMA-related capabilities, and network components such as SR-IOV support.
Consult the operator's compatibility matrix and installation guide: exact
custom resources, prerequisites, and supported combinations are versioned.

Understand the control flow: install prerequisites and the operator, configure
the required components, allow its controllers to reconcile nodes, then verify
the resulting pods and node resources. Kubernetes desired state does not
guarantee the host is ready; check device health, drivers, and relevant
Kubernetes events as well.

### RDMA device plugins and network attachments

**What:** Device plugins advertise hardware resources to the scheduler;
network attachments connect pods to additional networks using supported CNI
and RDMA components.

**Why:** GPU workloads need the right node resource and network path, not only
an ordinary pod interface.

**How:** Trace adapter and driver to device plugin, node resource, pod request,
attachment configuration, and pod-visible interface; test communication
between workloads.

Device plugins advertise supported hardware resources to the Kubernetes
scheduler so workloads can request them. A network attachment definition and
its CNI integration can connect a pod to an additional network; an RDMA-capable
attachment may expose a high-performance path when the host and configuration
support it. These are distinct from ordinary pod networking.

Follow the chain from physical adapter to host driver, device plugin, node
advertised resource, pod request, and pod-visible interface. Learn how resource
names and attachment configuration are defined in the chosen deployment.
Security, resource allocation, and topology alignment matter: a pod must land
on a node with the requested resource and a usable path to its peers.

### Deployment and verification

**What:** A version-aware process for installing the operator/components and
confirming the resulting Kubernetes and host network state.

**Why:** A ready operator pod does not prove that a workload received a
working RDMA-capable network path.

**How:** Check component readiness, node allocatable resources, pod scheduling,
interfaces/devices inside the workload, and a suitable end-to-end test.

Use the official deployment guide for the matching Kubernetes and operator
versions. Verify operator/controller health, component pod readiness on the
expected nodes, node allocatable resources, successful pod scheduling, and
interfaces/devices visible inside a test workload. Then run an appropriate
connectivity or RDMA test between pods/nodes; a `Running` pod alone is not a
network validation.

**Review questions:** Which component advertises devices to the scheduler?
How does a pod request the resource? What evidence proves that the pod has an
RDMA-capable path rather than only a normal network interface?

## 5. Troubleshooting Tools — 20%

**What:** Host, switch, fabric, and benchmark tools used to investigate
connectivity and performance symptoms.

**Why:** Choosing a tool that measures the wrong layer can create false
confidence or hide the actual failure domain.

**How:** Scope the incident, select the narrowest useful check, correlate
results and timestamps, and escalate from link state to end-to-end performance.

### A reliable troubleshooting sequence

**What:** A scoped, evidence-driven sequence from symptom definition through
physical/link, addressing, routing/policy, congestion, transport, and
application checks.

**Why:** Layered diagnosis reduces guesswork and avoids changing configuration
before the failure domain is understood.

**How:** Record endpoints, direction, timestamps, scope, and recent changes;
test one hypothesis at a time and capture before/after evidence.

Start by defining the symptom: affected workload, endpoints, direction,
start time, frequency, and recent changes. Scope whether it is one host, one
link, one rack, one tenant, or the whole fabric. Move from the physical and
link layers toward addressing, routing/partitioning, congestion, transport,
and application behavior. Change one variable at a time and capture
before/after state.

For every diagnostic command, know what device it runs on, what layer it
checks, what a healthy result looks like, and what it cannot prove. Command
options and output can vary by OS, driver, and software version; confirm syntax
with the installed tool's help and vendor documentation.

### Ethernet and switch diagnostics

**What:** Switch-level tools and telemetry for investigating drops, resource
limits, configuration state, and fabric-wide health.

**Why:** Host symptoms alone may not reveal the switch port, queue, or hardware
event responsible for an Ethernet/RoCE problem.

**How:** Select WJH for event context, NetQ for broader fabric context, and
`cl-resource-query` for supported switch resource questions; correlate with
host and port counters.

- **`cl-resource-query`:** inspect supported switch resource allocation and
  limits when a configuration or forwarding resource appears exhausted. Pair
  its output with the specific feature/configuration and switch logs; it is
  not a general end-to-end connectivity test.
- **WJH:** investigate reported packet-drop events and their switch-side
  reason/context. Correlate the event with the affected port, queue, time, and
  host symptoms.
- **NetQ:** use fabric-wide state and health views to determine whether
  configuration, topology, or operational issues are isolated or widespread.

### InfiniBand discovery and link tools

**What:** Host and fabric utilities that inspect HCA ports, discovered nodes,
reachability, topology, and link details.

**Why:** Different commands answer different questions; discovery, reachability,
and physical health are not interchangeable proofs.

**How:** Start with local `ibstat`, then use `ibnodes`, `ibping`,
`iblinkinfo`, `ibdiagnet`, or UFM according to the symptom and operational
scope.

- **`ibstat`:** inspect local HCA and port state, including link properties
  reported by the installed stack. Start here when one host cannot join or use
  the fabric.
- **`ibnodes`:** check which nodes are visible to the fabric tools. A missing
  node suggests discovery, link, SM, or configuration issues; it does not
  alone identify which one.
- **`ibping`:** perform a basic InfiniBand path/reachability check between
  endpoints when configured and permitted. It is a narrow test, not a
  throughput benchmark.
- **`iblinkinfo`:** inspect fabric link state and reported link details to
  narrow a topology-wide symptom to a port or connection.
- **`ibdiagnet`:** run a broader fabric diagnostic scan to discover topology
  and report supported errors or inconsistencies. Review impact and runtime
  before using extensive scans on a production fabric.
- **UFM health views:** combine fabric-wide monitoring with targeted checks on
  the links and devices implicated by the symptom.

### RDMA performance tools

**What:** Perftest utilities such as `ib_write_bw` and `ib_write_lat` measure
controlled RDMA bandwidth and latency between endpoints.

**Why:** They help determine whether an RDMA path meets an expected baseline
and narrow performance issues beyond simple reachability.

**How:** Use compatible client/server options, record message size and other
settings, run repeatable baselines, and compare like-for-like results while
monitoring host and fabric counters.

`ib_write_bw` and `ib_write_lat` are perftest utilities for measuring RDMA
write bandwidth and latency between configured endpoints. Use matching
software and compatible options on both sides, follow the tool's server/client
workflow, and record message size, queue depth, iterations, transport, and
other relevant settings. Run a baseline before drawing conclusions.

Benchmarks can consume resources and results depend on hardware, topology,
concurrency, CPU placement, and configuration. Compare like with like, test
both directions when relevant, and avoid treating one synthetic result as a
guarantee of application performance.

### Symptom-to-tool decision practice

**What:** A mapping from common symptoms to a first diagnostic check and
evidence-driven follow-up.

**Why:** It provides a disciplined starting point without assuming every
symptom has the same root cause.

**How:** Choose the row matching the observed scope, run the first checks, and
select the next test from the evidence rather than blindly executing every
tool.

| Symptom | First checks | Follow-up |
| --- | --- | --- |
| One host has no InfiniBand link | `ibstat`, host logs, cable/port | `iblinkinfo`, UFM, SM state |
| Expected endpoint is absent | `ibnodes`, host link state | `ibdiagnet`, UFM topology, cabling |
| Reachability fails between IB peers | local port state, addressing/partition | `ibping`, route/SM and PKey checks |
| Link is up but RDMA is slow | baseline perftest, counters, host errors | `ib_write_bw`, `ib_write_lat`, congestion and topology |
| Ethernet packets are reported dropped | switch port/queue and host counters | WJH event details, NetQ fabric context |
| Switch configuration/resource issue suspected | config state and logs | `cl-resource-query`, supported resource limits |

Treat this table as a starting point. Choose the next test based on evidence
and write down what each result rules in or out.

**Practice:** choose a fictional symptom, write the first three commands or
views you would use, predict healthy and unhealthy findings, and state the
next branch for each result.

## 6. Automation and Configuration — 10%

**What:** NVUE and Ansible methods for expressing, validating, and applying
repeatable network configuration.

**Why:** Automation reduces manual drift but can also amplify an incorrect
change across many devices.

**How:** Inspect desired and live state, validate changes on a canary, apply in
controlled batches, verify outcomes, and keep a rollback path.

### NVUE configuration workflow and templates

**What:** NVUE is a structured configuration and operational interface for
supported Cumulus Linux systems; templates reuse configuration patterns.

**Why:** Declarative, repeatable configuration can reduce drift while making
changes easier to review across devices.

**How:** Inspect current state, stage and validate intended changes, apply
using the documented release workflow, then verify operational state and
rollback readiness.

NVIDIA User Experience (NVUE) provides a structured way to configure and
inspect supported Cumulus Linux systems. Learn the distinction between
configuration intent, operational state, and the commands/API used to
manipulate them. A common workflow is to inspect current state, stage a
candidate change, review or validate it, apply/commit it, and verify resulting
operational state. Exact syntax and transaction behavior vary by release;
practice using the documentation for the target version.

Templates make a configuration pattern reusable across devices. Use variables
for device-specific values and keep shared intent consistent. Before rollout,
check interface names, platform support, dependencies, routing and QoS impact,
and the available rollback method. A successful configuration command does not
prove that links or protocols reached the intended state.

### Ansible playbooks for network configuration

**What:** Playbooks automate tasks against inventory targets using variables,
tasks, modules/APIs, conditions, and handlers.

**Why:** Automation improves repeatability and scale, but incorrect scope or
non-idempotent tasks can multiply operational errors.

**How:** Trace target hosts and variable values, validate with supported
check/diff modes, test on a canary, and inspect both task output and resulting
network state.

Ansible automates repeatable tasks across an inventory. Understand the basic
structure: inventory selects targets, variables supply values, tasks invoke
modules or APIs, and handlers can respond to changes. A playbook expresses
desired actions but may still be imperative depending on the module and task;
idempotency means rerunning it should not create unintended repeated changes.

Read a playbook by tracing the target hosts, privilege/context, variables,
conditions, module/API calls, and expected state. Review secrets handling,
check mode/diff support, error behavior, and how partial failures are reported.
Use a lab or staged rollout before applying network changes broadly.

### Safe rollout and verification

**What:** A staged change process with explicit validation criteria and
rollback conditions.

**Why:** Network changes can affect many hosts at once; a canary limits impact
and reveals unexpected behavior before wider deployment.

**How:** Validate/render first, apply to a small batch, check control and data
plane health against defined criteria, then expand or roll back.

Separate rendering/validation from applying changes. Apply to a small canary
set, inspect command/API output and device state, then expand in controlled
batches. Define success criteria and a rollback path in advance. After
automation, verify both the saved configuration and live state: interface
status, routing/neighbor sessions, QoS counters, and an appropriate end-to-end
test.

**Review questions:** What does the play target? Which values vary per device?
What makes a task safe to rerun? How do you detect a partial failure? What
would you verify after changing an NVUE template?

## Official resources

**What:** The certification blueprint and vendor learning sources that define
objectives, product behavior, and version-specific procedures.

**Why:** The study guide is an aid, not a replacement for current official
documentation or the exam's published scope.

**How:** Use the certification guide to scope objectives, then consult the
matching product/course documentation for details; note the version and access
date for technical claims.

- [NVIDIA NCP-AIN certification](https://www.nvidia.com/en-us/learn/certification/ai-networking-professional/)
- [Official NVIDIA exam study guide (PDF)](https://dam-cdn.nvd.orangelogic.com/AssetLink/32ljugfxg1hs1sd42371npw1xmcuo1yo.pdf)
- [InfiniBand Essentials](https://www.nvidia.com/en-us/training/academy/course-detail/?id=course%3A15139827)
- [InfiniBand Network Administration](https://www.nvidia.com/en-us/training/academy/course-detail/?id=course%3A15139854)
- [Cumulus Linux Essentials](https://www.nvidia.com/en-us/training/academy/course-detail/?id=course%3A15139853)

### Suggested readings

**What:** A topic-grouped collection of vendor courses, architecture
references, technical articles, and broader networking documentation.

**Why:** Reading across reference architectures, configuration guides, and
performance explanations helps connect exam concepts to real systems.

**How:** Follow the guided curriculum below, make your own notes, and verify
version-sensitive claims against the official product documentation.

These titles are a curated reading path to complement the chapter notes.
Unless a link is provided, search the exact title on the named publisher's
site; NVIDIA documentation and course pages may change URLs or require
enrollment. Read the source for its full context and version applicability.

### Guided study curriculum

**What:** A sequence of focused learning modules connecting the readings to
explanations, design exercises, and practical validation.

**Why:** Reading alone is not enough to demonstrate that you can explain a
concept or apply it to an unfamiliar network scenario.

**How:** Complete each module's study goal, read the listed sources, produce
the requested artifact, and answer the review questions without notes.

Use these modules to turn the reading list into an active study guide. The
notes below are original explanations and study tasks, not summaries of
paywalled or unprovided source text. Read the linked/vendor material for
platform-specific details, then record your own diagrams and lab output.

#### Module 1 — Map the AI factory

**What:** The system architecture and roles of compute, GPU interconnects,
BlueField, host adapters, switching, storage, and management.

**Why:** Understanding component boundaries makes capacity, isolation, and
failure analysis possible.

**How:** Study the named architecture sources, draw the block diagram, and
explain each connection and failure impact.

**Study goal:** explain how compute, scale-up links, scale-out fabric,
management, and storage fit together, and describe the role of each component.

An AI factory is a coordinated system, not just a GPU cluster. A useful
architecture sketch begins with GPU servers and their local GPU interconnects,
then shows host adapters, leaf/spine or other fabric tiers, storage services,
and management/control systems. Add the scalable-unit boundary: identify
which equipment and links are repeated when the design grows. NVIDIA
SuperPOD materials and the AI-networking architecture readings can help you
recognize these layers in a reference design.

BlueField is a programmable DPU platform. In a design, identify whether a
BlueField device is used for host-facing infrastructure services, network
connectivity, storage/security offloads, or another supported function. Do
not assume every deployment uses the same operating mode, interface ownership,
or service set: consult the appropriate BlueField documentation for the
product generation and software release.

**Work through the sources:** Key Components of the DGX SuperPOD; NVIDIA DGX
SuperPOD architecture readings; NVIDIA BlueField Networking Platform; and the
BlueField-3 Administrator Quick-Start Guide.

**Produce:** draw a block diagram that labels GPU/CPU, NVLink/NVSwitch, NIC or
SuperNIC, optional BlueField, leaf and spine, storage, and management. Use
different arrows for GPU payload traffic, storage traffic, and management
traffic. Add one sentence for each component describing what breaks or
degrades if it is unavailable.

**Check yourself:** Which links are scale-up and which are scale-out? Where
does the DPU sit relative to the host and fabric in the deployment you drew?
Which traffic shares physical infrastructure, and what isolation or QoS
controls are documented?

#### Module 2 — Reason about scalable units and rails

**What:** Repeatable infrastructure building blocks and the mapping of
GPU/network positions onto parallel rails.

**Why:** Scaling or miswiring a unit can change capacity and create shared
bottlenecks; rail alignment affects collective traffic distribution.

**How:** Map endpoint-to-switch connectivity, calculate the narrowest capacity
boundary, then evaluate the specified link/rail failure case.

**Study goal:** explain how a repeatable AI infrastructure unit scales and
how a rail-optimized topology distributes GPU traffic.

Start with the number of GPUs per node and the number and placement of network
interfaces. Draw each adapter port through its switch port and fabric tier;
keep separate lines for separate rails. A rail is useful only when endpoints,
cabling, switch connectivity, routing, and workload communication all align.
An apparently multi-rail design can still bottleneck on a shared uplink or an
uneven route.

Rail-optimized topology validation should be treated as an end-to-end check:
confirm the expected endpoint-to-rail mapping, validate physical connectivity,
and compare the discovered/operational topology against the intended design.
For each failure scenario, state whether traffic is lost, rerouted, or merely
slower; derive the answer from the design and platform behavior rather than
assuming failover.

**Work through the sources:** NVIDIA DGX SuperPOD and scalable-infrastructure
readings; Rail-Optimized Topology Validation; and the rail-optimized-networking
overview.

**Lab or paper exercise:** draw a two-rail, four-node fabric. Mark GPU 0 and
GPU 1, their NICs, switches, and uplinks. Trace an all-reduce on each rail.
Then remove one NIC link in the drawing and annotate affected ranks, remaining
capacity, possible path changes, and the counters or topology view that would
confirm the result.

**Check yourself:** What is repeated when one scalable unit is added? Which
links form the narrowest cut? Does the design provide independent failure
domains, or do both rails share a component? What evidence validates the
intended mapping?

#### Module 3 — Follow GPU communication and collectives

**What:** Intra-node and inter-node GPU transfers and collective operations
such as all-reduce, all-gather, reduce-scatter, and all-to-all.

**Why:** Communication schedules drive network traffic and synchronization;
one straggling rank or congested path can slow a whole workload.

**How:** Draw a collective's phases, trace an individual message end to end,
and compare expected traffic with topology and telemetry.

**Study goal:** distinguish intra-node GPU communication from inter-node
communication and describe how collective patterns create network traffic.

Within a supported system, GPUs can exchange data through NVLink/NVSwitch.
Across nodes, the path typically includes communication software, host/RDMA
setup, an adapter, the Ethernet/RoCE or InfiniBand fabric, a remote adapter,
and destination memory. GPUDirect RDMA can avoid a CPU staging copy on a
supported and correctly configured path, but it does not remove software
setup, permissions, completion handling, or compatibility requirements.

NCCL provides collective communication primitives used by GPU applications.
Learn the purpose of all-reduce, reduce-scatter, all-gather, and all-to-all.
Do not assume one fixed algorithm: a collective may use different schedules
according to message size, topology, library version, and configuration.
All-to-all can generate many concurrent exchanges; all-reduce can synchronize
participants so one slow rank delays completion. Interpret a performance
result in the context of the algorithm, link placement, message size, and
concurrency.

**Work through the sources:** Overview of NCCL; NVIDIA NVLink and NVSwitch;
and the NCCL all-to-all performance article.

**Produce:** for each collective, draw a four-rank example and mark who sends
to whom in each phase. Trace a single inter-node message from source GPU to
destination GPU. Note where payload is copied or directly accessed, where
completion is reported, and where congestion could delay the operation.

**Check yourself:** Why can an application report slow GPU communication when
all links are technically up? Why is peak NIC line rate not equivalent to
collective throughput? How could an imbalanced rail or straggling rank affect
iteration time?

#### Module 4 — Understand InfiniBand fabric operation

**What:** Subnet management, endpoint RDMA operation, fabric forwarding,
partition access, virtual lanes, and link flow control.

**Why:** Separating these mechanisms lets you distinguish a physical fault
from a discovery, addressing, permission, transport, or congestion issue.

**How:** Trace an operation from QP/HCA to destination completion and verify
each control and data-path layer in a lab or documented topology.

**Study goal:** explain how endpoints join an InfiniBand subnet, how traffic
is addressed and forwarded, and which controls affect reachability.

Begin at the physical port and HCA. A fabric manager/subnet manager discovers
devices and establishes required subnet configuration and path information.
Endpoints use adapter/transport state to send RDMA operations; switches
forward traffic along configured paths. The management/control process
configures the fabric but is not an extra switch hop for each data packet.

PKeys provide partition membership controls. Service levels and virtual lanes
affect traffic classification and link-level handling. Link-level credit
flow control prevents a sender from overrunning the receiver's available
buffer space on a link; it is not proof that an end-to-end path is free of
congestion. Keep these mechanisms distinct when diagnosing a failure:
physical link state, fabric discovery/path configuration, partition
permission, and application/transport setup are separate checks.

**Work through the sources:** InfiniBand Essentials; Aurelien Degremont and
Nathan Dauchy's LUG'24 material; Modes of Operation; and the InfiniBand Deep
Dive course. For course content that requires enrollment, use the course
directly and write your own notes rather than copying lesson text.

**Produce:** draw an RDMA operation from source queue pair/HCA through each
switch to the destination HCA and completion queue. Separately draw the SM
management relationship. Label endpoint addressing, PKey, service
level/virtual lane, and the checks you would use at each layer.

**Check yourself:** Which failure symptoms suggest cabling or link state?
Which suggest SM/discovery or path configuration? Which suggest PKey
membership? What does a successful reachability test prove—and not prove?

#### Module 5 — Operate and troubleshoot host/fabric interfaces

**What:** Host-side interface ownership/configuration and the evidence used to
diagnose or safely change adapter and fabric state.

**Why:** Host, adapter, switch, and manager views each expose different parts
of the path; disruptive operations can affect active workloads.

**How:** Capture baseline state, follow versioned documentation, use a
controlled change plan, and compare post-change logs/counters and test results.

**Study goal:** use host and fabric evidence together, and make safe operational
changes.

For a host-facing issue, determine which device owns each interface and which
operating mode is configured before changing state. Record current interface
configuration, link status, driver/firmware, logs, and relevant counters.
Follow the platform's documented change and reset procedures; resetting a
device can disrupt workloads and should not be treated as a routine diagnostic
shortcut.

Build a diagnostic ladder: confirm local adapter/port and host configuration;
confirm fabric discovery and paths; check the affected link and switch; test
reachability; then measure performance under controlled conditions. Logs and
timestamps help correlate events, but counters should be interpreted with
their reset interval and device context.

**Work through the sources:** Host-Side Interface Configuration; Logging;
BlueField-3 Administrator Quick-Start Guide; and BlueField Reset and Reboot
Procedure.

**Lab or paper exercise:** make a before/after checklist for one interface
change. Include the intended state, source documentation/version, pre-change
health, maintenance/impact note, validation test, rollback trigger, and
post-change logs/counters to capture.

**Check yourself:** How do you distinguish a link-up host interface from a
working RDMA path? Which evidence belongs to the host, adapter, switch, and
fabric manager? What is the impact of rebooting or resetting a BlueField or
adapter in the topology you are studying?

#### Module 6 — Compare InfiniBand and Spectrum-X Ethernet

**What:** Two scale-out fabric approaches and their respective packet
encapsulation, control, traffic treatment, congestion behavior, and diagnostics.

**Why:** Selecting the right test or interpreting a symptom depends on which
fabric mechanisms apply; similar symptoms can have different causes.

**How:** Build the comparison table, trace one GPU flow through each fabric,
and identify evidence at the endpoint, link, switch, and application layers.

**Study goal:** trace both traffic types and explain their different
congestion, control, and observability mechanisms.

For RoCEv2, trace RDMA traffic inside UDP/IP over an Ethernet underlay. Verify
addressing and MTU, traffic classification, queue/priority mapping, congestion
signaling, and the endpoint's response. ECN marking and PFC pausing have
different roles; validate their end-to-end configuration and counters rather
than treating either as a magic “lossless” switch.

For both Ethernet and InfiniBand, map a flow to physical links and queues.
Compare the failure domain, path selection, congestion response, and
diagnostic evidence. Spectrum-X whitepaper and technical articles describe
NVIDIA Ethernet design goals; SONiC material can provide broader operating
system context, but feature support and commands are platform/version
dependent.

**Work through the sources:** NVIDIA Spectrum-X Whitepaper; Turbocharging
Generative AI Workloads With NVIDIA Spectrum-X Networking Platform; Networking
for Data Centers and the Era of AI; and SONiC Wiki.

**Produce:** create a side-by-side table for RoCEv2 and InfiniBand covering
encapsulation/addressing, fabric control, congestion/flow control, QoS
constructs, common host checks, and fabric diagnostics. Then trace one
cross-node GPU flow in each fabric and mark where you would inspect drops,
congestion, link health, and endpoint completion.

**Check yourself:** Why does IP ping not verify RoCE? How are ECN and PFC
different? Which observations distinguish endpoint limitations from a
congested fabric path? Which details must be checked against the exact
product and software release?

#### Capstone — explain and validate one design

**What:** An integrated explanation of one reference topology, capacity
assumptions, GPU traffic, failure behavior, and validation plan.

**Why:** Real deployments combine components and failure domains; isolated
definitions are not enough to reason about end-to-end behavior.

**How:** Complete the six deliverables below, cite the source for design
assumptions, and mark anything the source does not establish as an open question.

Choose a reference topology from the suggested NVIDIA architecture readings.
Create a one-page design brief containing:

1. A topology diagram with compute, GPUs, BlueField where present, NICs,
   switches, rails, storage, and management.
2. A capacity calculation for a representative communication boundary,
   stating port rates, number of links, oversubscription assumptions, and
   failure case.
3. One GPU-to-GPU flow trace for an intra-node path and one for an inter-node
   RDMA path.
4. One collective communication example and the network behavior it creates.
5. A failure tree covering link loss, endpoint misconfiguration, partition or
   policy mismatch, and congestion.
6. A validation plan listing expected evidence, the tools or dashboards to
   consult, and what each test cannot prove.

Explain every diagram in your own words. If you cannot identify a component,
boundary, or assumption in the source material, mark it as an open question
instead of guessing.

#### InfiniBand foundations and operations

**What:** Learning sources for InfiniBand operation, host configuration,
management modes, and troubleshooting.

**Why:** They deepen understanding of the control plane, endpoint behavior,
and operational checks beyond a high-level fabric diagram.

**How:** Read the fundamentals first, then compare host-side and fabric-side
procedures; record commands and expected state from the applicable release.

- [InfiniBand Essentials | NVIDIA Academy](https://www.nvidia.com/en-us/training/academy/course-detail/?id=course%3A15139827)
- Aurelien Degremont and Nathan Dauchy, LUG'24 (May 7–8, 2024)
- Modes of Operation (NVIDIA Docs)
- Host-Side Interface Configuration (NVIDIA Docs)
- Logging (NVIDIA Docs)
- [InfiniBand Deep Dive (Udemy)](https://www.udemy.com/course/infiniband-deep-dive/learn/lecture/56215196#overview) — course access may require a Udemy account or enrollment. Add your own takeaways and lab observations after completing the lessons.

#### AI factory architecture and NVIDIA systems

**What:** Reference architectures and system descriptions for GPU-based
clusters and AI infrastructure.

**Why:** They show how compute, networking, storage, management, and power
constraints are assembled in deployable systems.

**How:** Sketch the architecture in layers and label traffic paths, scaling
boundaries, and any assumptions the source leaves platform-specific.

- NVIDIA DGX SuperPOD: AI Infrastructure for Enterprise Deployments
- Key Components of the DGX SuperPOD (NVIDIA Docs)
- NVIDIA DGX SuperPOD: Scalable Infrastructure for AI Leadership
- NVIDIA GB200 NVL72 Delivers Trillion-Parameter LLM Training and Real-Time Inference (NVIDIA Technical Blog)
- NVIDIA Unveils Reference Architecture for AI Cloud Providers (NVIDIA Blog)
- Networking for Data Centers and the Era of AI (NVIDIA Technical Blog)

#### BlueField and host interfaces

**What:** Product documentation about BlueField networking, administration,
host interfaces, and lifecycle operations.

**Why:** Interface ownership and operating mode affect the traffic path and
the correct way to configure or troubleshoot a deployment.

**How:** Identify product/software versions and operating mode first; use the
matching guide to record interface state, change procedure, and verification.

- BlueField-3 Administrator Quick-Start Guide (NVIDIA Docs)
- NVIDIA BlueField Networking Platform
- NVIDIA BlueField Reset and Reboot Procedure (NVIDIA Docs)

#### GPU communication, collectives, and rails

**What:** Learning sources about GPU interconnects, collective libraries,
rail topology, and communication performance.

**Why:** The communication algorithm and topology together determine which
links carry traffic and where synchronization or imbalance can limit jobs.

**How:** Draw collective phases across ranks, map ranks to GPUs/NICs/rails, and
compare predicted traffic with documented validation or benchmark results.

- Overview of NCCL (NCCL documentation)
- Doubling all2all Performance With NVIDIA Collective Communication Library 2.12 (NVIDIA Technical Blog)
- NVIDIA NVLink and NVSwitch: Fastest HPC Data Center Platform
- Rail-Optimized Topology Validation (NVIDIA Docs)
- Rail-Optimised Networking: How NVIDIA Is Rethinking AI Network Design in the Data Centre (Vespertec)

#### Spectrum-X and Ethernet fabrics

**What:** NVIDIA Ethernet platform material and broader network operating
system documentation.

**Why:** These sources provide context for scale-out Ethernet, AI workload
performance, and fabric operations.

**How:** Separate platform-specific claims from general Ethernet concepts and
verify supported features and commands for the exact hardware/software
release.

- NVIDIA Spectrum-X Whitepaper
- Turbocharging Generative AI Workloads With NVIDIA Spectrum-X Networking Platform (NVIDIA Technical Blog)
- SONiC Wiki

When adding notes, prefer your own explanations and cite external sources.
Avoid committing credentials, exam questions, or materials you do not have
permission to redistribute.
