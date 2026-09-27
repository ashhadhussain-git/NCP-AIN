---
description: Personal study guide and lab notes for the NVIDIA-Certified Professional AI Networking exam.
---

# NCP-AIN Study Notes

Detailed personal study notes for the NVIDIA-Certified Professional: AI
Networking (NCP-AIN) exam. Use the explanations and exercises below as a
starting point, then add your own diagrams, command output, lab results, and
questions as you study.

> [!NOTE]
> Exam weights and objectives can change. Check the official NVIDIA resources
> before using this outline to plan your final review.

> **Reading this guide**
> Use [`SUMMARY.md`](./SUMMARY.md) as the chapter index. Each domain below is
> organized as a chapter with focused topics, practical exercises, and review
> prompts. The guide is designed for study and lab practice, not as a
> production deployment runbook.

## Table of contents

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
| [Official resources](#official-resources) | — | Vendor docs and courses |

---

## Study plan

- [ ] Week 1: AI data center foundations
- [ ] Weeks 2–3: Spectrum networking; practice in NVIDIA Air where available
- [ ] Week 4: InfiniBand networking
- [ ] Week 5: Troubleshooting and automation
- [ ] Week 6: Kubernetes integration, review, and timed practice

Mark a week complete as you finish it. Spend extra review time on the two
30%-weight domains and revisit topics you find difficult.

## Topology case studies and packet flows

The examples below are illustrative learning scenarios, not prescriptive
production designs. Real designs depend on the selected NVIDIA platform,
software release, workload, scale, cabling, and validated deployment
documentation. The official [NVIDIA NCP-AIN exam study guide](https://dam-cdn.nvd.orangelogic.com/AssetLink/32ljugfxg1hs1sd42371npw1xmcuo1yo.pdf)
is the reference for the exam objectives; these explanations and diagrams are
original study notes to help reason through those objectives.

### Case study 1: two-tier leaf-spine AI fabric

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

### AI factory architecture and components

An AI factory is designed to turn data into trained or served models. Its
compute, storage, power, cooling, and network capacity must be planned as one
system. Large GPU jobs create many synchronized flows; a slow or oversubscribed
network can leave expensive accelerators waiting instead of computing.

Know the function and failure impact of the main building blocks:

- **GPU and GPU server:** perform accelerated computation and host one or more
  network adapters.
- **NVLink/NVSwitch:** provide high-bandwidth communication among GPUs within
  a server or supported system. They do not replace the inter-server fabric.
- **NIC/SuperNIC:** connects a host to an Ethernet fabric and may offload
  networking and congestion-related work.
- **DPU:** a programmable data-processing unit that can offload infrastructure
  services such as networking, security, or storage from the host CPU.
- **Leaf and spine switches:** form the scalable switching fabric connecting
  hosts and, at higher tiers, leaf switches.
- **Storage and management networks:** serve different traffic and operational
  needs from the GPU data path; understand their purpose and isolation.

When estimating capacity, distinguish link rate from usable application
throughput. Account for the number of endpoints, uplink capacity, path count,
oversubscription, protocol overhead, and whether all nodes communicate at once.
Power, cooling, cabling distance, and rack density constrain which theoretical
topology can actually be deployed.

### Scalable units and leaf-spine design

A scalable unit (SU) is a repeatable building block of compute and networking.
Replicating a known-good unit simplifies capacity planning, cabling, validation,
and fault isolation. Be able to explain what grows when another unit is added
and which inter-unit links or services could become bottlenecks.

In a basic leaf-spine fabric, each host attaches to a leaf, and each leaf
connects to every spine. Paths between hosts in different leaf blocks usually
have a predictable number of switch hops. Multiple equal-cost paths can provide
aggregate capacity and resilience, provided routing and link utilization are
working as intended.

Draw a small topology and trace traffic between two hosts on one leaf and on
different leaves. Identify the links shared by many flows. Calculate a simple
oversubscription ratio as total offered downlink bandwidth divided by total
uplink bandwidth; a ratio above 1 means not all host ports can run at line rate
simultaneously toward the rest of the fabric.

### Rail-optimized topologies

In a rail-optimized GPU cluster, matching GPU positions across servers connect
through corresponding network rails. For example, GPU/NIC position 0 in each
server uses rail 0, while position 1 uses rail 1. This gives collective
communication patterns more independent paths and can reduce contention
between unrelated GPU flows.

Understand the topology, not just the label: map each GPU to its local NIC,
switch port, leaf, and uplink. Then follow an all-reduce or all-to-all exchange
across several nodes. Explain how multiple rails provide parallelism, and what
happens to bandwidth or resiliency if one rail or a link fails. A rail design
still depends on correct cabling, routing, balanced traffic, and enough
end-to-end capacity.

### Intra-node vs. inter-node GPU communication

Within a server, GPUs can exchange data over NVLink/NVSwitch when the platform
supports it. Between servers, data traverses a network adapter and the
Ethernet/RoCE or InfiniBand fabric. The two paths have different hardware,
failure modes, and observability; a healthy inter-node fabric does not prove
intra-node GPU links are healthy, or vice versa.

Trace an application transfer in both cases. For inter-node traffic identify
the GPU, host software, adapter, fabric path, remote adapter, and destination
GPU. Consider how collective operations synchronize many of these transfers:
incast, synchronized bursts, or an imbalanced path can affect job completion
time even when average link utilization looks acceptable.

### RDMA and GPUDirect concepts

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

### Spectrum-X and RoCE configuration concepts

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

### QoS, ECN, and PFC

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

### Adaptive routing and telemetry

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

### BGP EVPN, VTEPs, and VNIs

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

### NVIDIA Air

NVIDIA Air is a network simulation environment useful for learning and
validating supported topologies and configurations without first changing a
production fabric. Treat simulation results as evidence for the simulated
features only: it cannot prove physical cabling, optics, actual hardware
capacity, or behavior of features not represented by the environment.

Use a lab to practice configuration changes, expected state, and failure
scenarios. Save the topology, assumptions, commands, and before/after output
with your notes. Confirm current access and feature availability in NVIDIA's
documentation.

### What Just Happened (WJH) and NetQ

What Just Happened (WJH) helps investigate switch events such as packet drops
and their reported causes. Use it to narrow a specific event to a port, reason,
or relevant hardware context, then correlate its timestamp and counters with
the host and other switches. A reported drop reason is a clue to validate, not
by itself a complete end-to-end root cause.

NetQ provides broader fabric operations and visibility, including topology and
health information depending on the deployed version and configuration. Use
it to identify whether an issue is isolated or spans multiple devices, and to
compare configuration or operational state across the fabric. Know when to
use event-level switch evidence (WJH) versus fabric-wide context (NetQ); neither
replaces checking endpoint drivers, application symptoms, and physical links.

### DOCA and SuperNIC

DOCA is NVIDIA's software development framework for supported DPUs and
networking platforms. It includes APIs, libraries, and tools; it is not a
single switch command or a synonym for all networking software. Understand
which host or DPU component runs a given service and which device/driver
versions it requires.

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

### Fabric bring-up and Subnet Manager high availability

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

### NVIDIA Network Operator

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

### A reliable troubleshooting sequence

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

### NVUE configuration workflow and templates

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

- [NVIDIA NCP-AIN certification](https://www.nvidia.com/en-us/learn/certification/ai-networking-professional/)
- [Official NVIDIA exam study guide (PDF)](https://dam-cdn.nvd.orangelogic.com/AssetLink/32ljugfxg1hs1sd42371npw1xmcuo1yo.pdf)
- [InfiniBand Essentials](https://www.nvidia.com/en-us/training/academy/course-detail/?id=course%3A15139827)
- [InfiniBand Network Administration](https://www.nvidia.com/en-us/training/academy/course-detail/?id=course%3A15139854)
- [Cumulus Linux Essentials](https://www.nvidia.com/en-us/training/academy/course-detail/?id=course%3A15139853)

### Additional learning

- [InfiniBand Deep Dive (Udemy)](https://www.udemy.com/course/infiniband-deep-dive/learn/lecture/56215196#overview) — course access may require a Udemy account or enrollment. Add your own takeaways and lab observations after completing the lessons.

When adding notes, prefer your own explanations and cite external sources.
Avoid committing credentials, exam questions, or materials you do not have
permission to redistribute.
