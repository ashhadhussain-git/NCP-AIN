# NCP-AIN Study Notes

Personal learning notes for the NVIDIA-Certified Professional: AI Networking
(NCP-AIN) exam. This repository starts with an outline; add your own summaries,
diagrams, command examples, lab results, and questions as you study each topic.

> Exam weights and objectives can change. Check the official NVIDIA resources
> before using this outline to plan your final review.

## Table of contents

- [Study plan](#study-plan)
- [AI Data Center Design and Optimization — 5%](#1-ai-data-center-design-and-optimization--5)
- [NVIDIA Spectrum Networking — 30%](#2-nvidia-spectrum-networking--30)
- [NVIDIA InfiniBand Networking — 30%](#3-nvidia-infiniband-networking--30)
- [Kubernetes Integration — 5%](#4-kubernetes-integration--5)
- [Troubleshooting Tools — 20%](#5-troubleshooting-tools--20)
- [Automation and Configuration — 10%](#6-automation-and-configuration--10)
- [Official resources](#official-resources)

## Study plan

- [ ] Week 1: AI data center foundations
- [ ] Weeks 2–3: Spectrum networking; practice in NVIDIA Air where available
- [ ] Week 4: InfiniBand networking
- [ ] Week 5: Troubleshooting and automation
- [ ] Week 6: Kubernetes integration, review, and timed practice

Mark a week complete as you finish it. Spend extra review time on the two
30%-weight domains and revisit topics you find difficult.

## 1. AI Data Center Design and Optimization — 5%

- [ ] AI factory architecture and components
- [ ] Scalable units and leaf-spine design
- [ ] Rail-optimized topologies
- [ ] Intra-node vs. inter-node GPU communication
- [ ] RDMA and GPUDirect concepts

### Study notes

Add your own explanation, diagram, or example here as you learn.

## 2. NVIDIA Spectrum Networking — 30%

- [ ] Spectrum-X and RoCE configuration concepts
- [ ] QoS, ECN, and PFC
- [ ] Adaptive routing and telemetry
- [ ] BGP EVPN, VTEPs, and VNIs
- [ ] NVIDIA Air
- [ ] What Just Happened (WJH) and NetQ
- [ ] DOCA and SuperNIC

### Study notes

Add your own explanation, configuration examples, and lab observations here.

## 3. NVIDIA InfiniBand Networking — 30%

- [ ] Fabric bring-up and Subnet Manager high availability
- [ ] Partition keys (PKeys) and membership
- [ ] QoS, virtual lanes, and adaptive routing
- [ ] Unified Fabric Manager (UFM)

### Study notes

Add your own explanation, diagrams, and lab observations here.

## 4. Kubernetes Integration — 5%

- [ ] NVIDIA Network Operator
- [ ] RDMA device plugins and network attachments
- [ ] Operator deployment and verification

### Study notes

Add your own deployment notes and verification steps here.

## 5. Troubleshooting Tools — 20%

- [ ] `cl-resource-query`
- [ ] WJH and UFM health diagnostics
- [ ] `ibping`, `ibstat`, and `ibnodes`
- [ ] `ibdiagnet` and `iblinkinfo`
- [ ] `ib_write_bw` and `ib_write_lat`
- [ ] Build a symptom-to-tool troubleshooting checklist

### Study notes

For each tool, record what it checks, a useful example, and what its output
helped you diagnose.

## 6. Automation and Configuration — 10%

- [ ] NVUE configuration workflow and templates
- [ ] Ansible playbooks for network configuration
- [ ] Review and explain the network state produced by an automation example

### Study notes

Add your own playbook examples and explanations here.

## Official resources

- [NVIDIA NCP-AIN certification](https://www.nvidia.com/en-us/learn/certification/ai-networking-professional/)
- [Official NVIDIA exam study guide (PDF)](https://dam-cdn.nvd.orangelogic.com/AssetLink/32ljugfxg1hs1sd42371npw1xmcuo1yo.pdf)
- [InfiniBand Essentials](https://www.nvidia.com/en-us/training/academy/course-detail/?id=course%3A15139827)
- [InfiniBand Network Administration](https://www.nvidia.com/en-us/training/academy/course-detail/?id=course%3A15139854)
- [Cumulus Linux Essentials](https://www.nvidia.com/en-us/training/academy/course-detail/?id=course%3A15139853)

When adding notes, prefer your own explanations and cite external sources.
Avoid committing credentials, exam questions, or materials you do not have
permission to redistribute.
