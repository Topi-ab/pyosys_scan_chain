from pyosys import libyosys as ys

from dataclasses import dataclass, field

def fresh_id(prefix: str = None) -> ys.IdString:
    if prefix is None:
        prefix = "$auto$"
    r = ys.IdString.new_autoidx_with_prefix(prefix)
    return r

class TestClass:
    @dataclass
    class ModuleEntry:
        scan_chains: dict[ys.Wire, "TestClass.ModuleEntry.ScanInfo"] = field(default_factory=dict)
        enable_port: ys.Wire = None

        @dataclass
        class ScanInfo:
            scan_in: ys.Wire
            scan_out: ys.Wire
            dff_cnt: int = 0

    def __init__(self, design: ys.Design, top_module: ys.Module):
        self._design = design
        self._top_module = top_module
        self._modules_ports = []
        self._module_muxes = []
        self.ModuleScanportInfo: dict[ys.Module, TestClass.ModuleEntry] = {}
        self.ModuleDepthInfo: dict[ys.Module, int] = {}

    def processModuleDepth(self, module: ys.Module) -> int:
        has_children = False
        r = 0
        max_depth = 0
        cells = list(module.cells_.values())
        for cell in cells:
            if cell.type in self._design.modules_:
                has_children = True
                submod = self._design.modules_[cell.type]
                sub_depth = self.processModuleDepth(submod)
                max_depth = max(max_depth, sub_depth)
                r = max_depth + 1
        self.ModuleDepthInfo[module] = r
        return r

    def ModulesByDepth(self):
        assert len(self.ModuleDepthInfo) > 0, "Module depth information not processed yet."
        return sorted(self.ModuleDepthInfo, key=self.ModuleDepthInfo.get)
    
    def processClocks(self):
        for module in self.ModulesByDepth():
            cells = list(module.cells_.values())
            clocks: dict[ys.Wire, int] = {}
            for cell in cells:
                if cell.is_builtin_ff():
                    clk_port = cell.getPort("\\CLK").as_wire()
                    polarity = cell.getParam("\\CLK_POLARITY").as_int()
                    assert polarity == 1, "Unsupported clock polarity. Only positive edge supported."
                    assert clk_port.port_input, "Clock port is not input port. Unsupported clocking mode."
                    if clk_port not in clocks:
                        clocks[clk_port] = 1
                    else:
                        clocks[clk_port] += 1
                if cell.type in self._design.modules_:
                    submod = self._design.modules_[cell.type]
                    submod_clocks_info = self.ModuleScanportInfo.get(submod)
                    if submod_clocks_info is not None:
                        for clk in submod_clocks_info.scan_chains:
                            scan_info = submod_clocks_info.scan_chains[clk]
                            clk_port = cell.getPort(clk.name).as_wire()
                            if clk_port not in clocks:
                                clocks[clk_port] = scan_info.dff_cnt
                            else:
                                clocks[clk_port] += scan_info.dff_cnt
            if self.ModuleScanportInfo.get(module) is None:
                self.ModuleScanportInfo[module] = TestClass.ModuleEntry()
                x = self.ModuleScanportInfo[module].scan_chains
                if self.ModuleScanportInfo[module].scan_chains is None:
                    self.ModuleScanportInfo[module].scan_chains = []
            for clk in clocks:
                e = TestClass.ModuleEntry.ScanInfo(
                    scan_in=None,
                    scan_out=None,
                    dff_cnt=clocks[clk]
                )
                self.ModuleScanportInfo[module].scan_chains[clk] = e

    def EnumerateClocks(self, module: ys.Module):
        clocks = set()
        cells = list(module.cells_.values())
        for cell in cells:
            if cell.is_builtin_ff():
                clk_port = cell.getPort("\\CLK").as_wire()
                polarity = cell.getParam("\\CLK_POLARITY").as_int()
                assert polarity == 1, "Unsupported clock polarity. Only positive edge supported."
                assert clk_port.port_input, "Clock port is not input port. Unsupported clocking mode."
                clocks.add(clk_port)
        i = 0
        r = set()
        for clk in clocks:
            r.add((i, clk))
            i += 1
        return r
    
    def generateModulePorts(self):
        for module in self.ModulesByDepth():
            info = self.ModuleScanportInfo.get(module)
            assert info is not None, "Module scan port information not found."

            en_port = module.addWire("$scan_enable_in")
            en_port.port_input = True

            i = 0
            for clk in info.scan_chains:
                scan_in_port = module.addWire(f"$scan_{i}_in")
                scan_in_port.port_input = True
                scan_out_port = module.addWire(f"$scan_{i}_out")
                scan_out_port.port_output = True
                self.ModuleScanportInfo[module].scan_chains[clk].scan_in = scan_in_port
                self.ModuleScanportInfo[module].scan_chains[clk].scan_out = scan_out_port
                i += 1
            self.ModuleScanportInfo[module].enable_port = en_port
            module.fixup_ports()

    
    def generateMuxes(self):
        # TODO: detect also $fsm.
        # TODO: Separate mechanism for memories.
        # TODO: Clock polarity.

        # DFF types:
        # $sr $ff $dff $dffe $adff $adffe $aldff $aldffe $sdff $sdffe $sdffce $dffsr $dffsre $dlatch $adlatch $dlatchsr
        
        # DFF ports:
        # CLK, D, Q, EN, SET, CLR, ARST, ALOAD, AD, SRST
        
        for module in self.ModulesByDepth():
            print(f'Creataing a scan chain to module: {module.name.str()}')
            info = self.ModuleScanportInfo.get(module)
            assert info is not None, "Module scan port information not found."
            flops: dict[ys.Wire, set[list[ys.Cell]]] = {}
            cells = list(module.cells_.values())
            for cell in cells:
                if cell.is_builtin_ff():
                    clk_port = cell.getPort("\\CLK").as_wire()
                    assert clk_port in info.scan_chains, "Clock port not found in module scan port information."
                    if flops.get(clk_port) is None:
                        flops[clk_port] = set()
                    flops[clk_port].add(cell)
                if cell.type in self._design.modules_:
                    submod = self._design.modules_[cell.type]
                    submod_info = self.ModuleScanportInfo.get(submod)
                    assert submod_info is not None, "Submodule scan port information not found."
                    for clk in submod_info.scan_chains:
                        clk_port = cell.getPort(clk.name).as_wire()
                        assert clk_port in info.scan_chains, "Clock port not found in module scan port information."
                        if flops.get(clk_port) is None:
                            flops[clk_port] = set()
                        flops[clk_port].add(cell)
            for clk in flops:
                print(f' Generating scan chain for clock: {clk.name.str()}')
                en_port = ys.SigSpec(module.wire("$scan_enable_in"))
                scan_in_port = ys.SigSpec(info.scan_chains[clk].scan_in)
                scan_out_port = ys.SigSpec(info.scan_chains[clk].scan_out)
                dff_set = set()
                for cell in flops[clk]:
                    if cell.is_builtin_ff():
                        type = cell.type.str()
                        match type:
                            case "$ff" | "$dff" | "$dffe" | "$adff" | "$adffe" | "$aldff" | "$aldffe" | "$sdff" | "$sdffe" | "$sdffce" | "$dffsr" | "$dffsre":
                                has_en = False
                                has_set = False
                                has_clr = False
                                has_arst = False
                                has_aload = False
                                has_srst = False

                                match type:
                                    case "$dffe" | "$adffe" | "$aldffe" | "$sdffe" | "$sdffce":
                                        has_en = True
                                match type:
                                    case "$dffsr" | "$dffsre":
                                        has_set = True
                                        has_clr = True
                                match type:
                                    case "$adff" | "$adffe" | "$aldff" | "$aldffe":
                                        has_arst = True
                                match type:
                                    case "$aldff" | "$aldffe":
                                        has_aload = True
                                match type:
                                    case "$sdff" | "$sdffe" | "$sdffce":
                                        has_srst = True
                                
                                if has_en:
                                    polarity = cell.getParam("\\EN_POLARITY").as_int()
                                    orig_en = ys.SigSpec(cell.getPort("\\EN"))
                                    new_en = ys.SigSpec(module.addWire(fresh_id(), 1))
                                    if polarity == 1:
                                        or_en = module.addOr(fresh_id(), orig_en, en_port, new_en, False, "scan chain enable mux")
                                    else:
                                        en_port_n = ys.SigSpec(module.addWire(fresh_id(), 1))
                                        not_en = module.addNot(fresh_id(), en_port, en_port_n, False, "scan chain enable inverter")
                                        and_en = module.addAnd(fresh_id(), orig_en, en_port_n, new_en, False, "scan chain enable mux")
                                    cell.setPort("\\EN", new_en)
                                
                                if has_arst:
                                    polarity = cell.getParam("\\ARST_POLARITY").as_int()
                                    orig_arst = ys.SigSpec(cell.getPort("\\ARST"))
                                    new_arst = ys.SigSpec(module.addWire(fresh_id(), 1))
                                    if polarity == 1:
                                        en_port_n = ys.SigSpec(module.addWire(fresh_id(), 1))
                                        not_en = module.addNot(fresh_id(), en_port, en_port_n, False, "scan chain arst inverter")
                                        and_arst = module.addAnd(fresh_id(), orig_arst, en_port_n, new_arst, False, "scan chain arst mux")
                                    else:
                                        or_arst = module.addOr(fresh_id(), orig_arst, en_port, new_arst, False, "scan chain arst mux")
                                    cell.setPort("\\ARST", new_arst)

                                if has_aload:
                                    polarity = cell.getParam("\\ALOAD_POLARITY").as_int()
                                    orig_aload = ys.SigSpec(cell.getPort("\\ALOAD"))
                                    new_aload = ys.SigSpec(module.addWire(fresh_id(), 1))
                                    if polarity == 1:
                                        en_port_n = ys.SigSpec(module.addWire(fresh_id(), 1))
                                        not_en = module.addNot(fresh_id(), en_port, en_port_n, False, "scan chain aload inverter")
                                        and_aload = module.addAnd(fresh_id(), orig_aload, en_port_n, new_aload, False, "scan chain aload mux")
                                    else:
                                        or_aload = module.addOr(fresh_id(), orig_aload, en_port, new_aload, False, "scan chain aload mux")
                                    cell.setPort("\\ALOAD", new_aload)
                                
                                if has_srst:
                                    polarity = cell.getParam("\\SRST_POLARITY").as_int()
                                    orig_srst = ys.SigSpec(cell.getPort("\\SRST"))
                                    new_srst = ys.SigSpec(module.addWire(fresh_id(), 1))
                                    if polarity == 1:
                                        en_port_n = ys.SigSpec(module.addWire(fresh_id(), 1))
                                        not_en = module.addNot(fresh_id(), en_port, en_port_n, False, "scan chain srst inverter")
                                        and_srst = module.addAnd(fresh_id(), orig_srst, en_port_n, new_srst, False, "scan chain srst mux")
                                    else:
                                        or_srst = module.addOr(fresh_id(), orig_srst, en_port, new_srst, False, "scan chain srst mux")
                                    cell.setPort("\\SRST", new_srst)
                                    
                                if has_set:
                                    width = cell.getParam("\\WIDTH").as_int()
                                    polarity = cell.getParam("\\SET_POLARITY").as_int()

                                    setPort = cell.getPort("\\SET")
                                    setWire = module.addWire(fresh_id(), width)

                                    orig_a: list[ys.SigSpec] = []
                                    new_a: list[ys.SigSpec] = []
                                    if width == 1:
                                        orig_a.append(ys.SigSpec(setPort))
                                        new_a.append(ys.SigSpec(setWire))
                                    else:
                                        for i in range(width):
                                            orig_a.append(ys.SigSpec(ys.SigSpec(setPort)[i], 1))
                                            new_a.append(ys.SigSpec(ys.SigSpec(setWire)[i], 1))

                                    used_enable = en_port
                                    if polarity == 1:
                                        en_port_n = ys.SigSpec(module.addWire(fresh_id(), 1))
                                        not_en = module.addNot(fresh_id(), en_port, en_port_n, False, "scan chain set inverter")
                                        used_enable = en_port_n
                                        for i in range(width):
                                            and_set = module.addAnd(fresh_id(), orig_a[i], used_enable, new_a[i], False, "scan chain and as set mux")
                                    else:
                                        for i in range(width):
                                            or_set = module.addOr(fresh_id(), orig_a[i], used_enable, new_a[i], False, "scan chain or as set mux")

                                    cell.setPort("\\SET", ys.SigSpec(setWire))
                                
                                if has_clr:
                                    width = cell.getParam("\\WIDTH").as_int()
                                    polarity = cell.getParam("\\CLR_POLARITY").as_int()

                                    clrPort = cell.getPort("\\CLR")
                                    clrWire = module.addWire(fresh_id(), width)

                                    orig_a: list[ys.SigSpec] = []
                                    new_a: list[ys.SigSpec] = []
                                    if width == 1:
                                        orig_a.append(ys.SigSpec(clrPort))
                                        new_a.append(ys.SigSpec(clrWire))
                                    else:
                                        for i in range(width):
                                            orig_a.append(ys.SigSpec(ys.SigSpec(clrPort)[i], 1))
                                            new_a.append(ys.SigSpec(ys.SigSpec(clrWire)[i], 1))

                                    used_enable = en_port
                                    if polarity == 1:
                                        en_port_n = ys.SigSpec(module.addWire(fresh_id(), 1))
                                        not_en = module.addNot(fresh_id(), en_port, en_port_n, False, "scan chain clr inverter")
                                        used_enable = en_port_n
                                        for i in range(width):
                                            and_clr = module.addAnd(fresh_id(), orig_a[i], used_enable, new_a[i], False, "scan chain clr and as mux")
                                    else:
                                        for i in range(width):
                                            or_clr = module.addOr(fresh_id(), orig_a[i], used_enable, new_a[i], False, "scan chain clr or as mux")

                                    cell.setPort("\\CLR", ys.SigSpec(clrWire))

                                orig_d = cell.getPort("\\D")
                                orig_q = cell.getPort("\\Q")
                                width = orig_d.size()
                                new_d = module.addWire(fresh_id(), width)
                                mux_y = module.addWire(fresh_id(), width)
                                mux = module.addMux(fresh_id(), ys.SigSpec(orig_d), ys.SigSpec(new_d), ys.SigSpec(en_port), ys.SigSpec(mux_y), "scan chain data mux")
                                cell.setPort("\\D", ys.SigSpec(mux_y))
                                dff_set.add((new_d, orig_q, width))
                            case _:
                                raise Exception(f'"Unsupported flip-flop type: {type}"')
                    elif cell.type in self._design.modules_:
                        submod_info = self.ModuleScanportInfo.get(self._design.modules_[cell.type])
                        assert submod_info is not None, "Submodule scan port information not found."
                        e_port = submod_info.enable_port
                        cell.setPort(e_port.name, en_port)
                        for sub_clk in submod_info.scan_chains:
                            e = submod_info.scan_chains[sub_clk]
                            if cell.getPort(sub_clk.name).as_wire() is clk:
                                s_in = module.addWire(fresh_id(), 1)
                                s_out = module.addWire(fresh_id(), 1)
                                cell.setPort(e.scan_in.name, ys.SigSpec(s_in))
                                cell.setPort(e.scan_out.name, ys.SigSpec(s_out))
                                dff_set.add((s_in, s_out, 1))
                
                scan_in = scan_in_port
                for new_d, orig_q, cnt in dff_set:
                    for i in range(new_d.width):
                        a = scan_in
                        b = ys.SigSpec(new_d)[i]
                        c = ys.SigSpec(b, 1)
                        module.connect(c, a)
                        d = ys.SigSpec(orig_q)[i]
                        e = ys.SigSpec(d, 1)
                        scan_in = e
                module.connect(scan_out_port, scan_in)

    def ScanInfo(self) -> str:
        r = ""
        for clk in self.ModuleScanportInfo[self._top_module].scan_chains:
            scan_info = self.ModuleScanportInfo[self._top_module].scan_chains[clk]
            r += f'Clock: {clk.name.str()}\n'
            r += f'\tFF count: {scan_info.dff_cnt}\n'
            r += f'\tscan input port: {scan_info.scan_in.name.str()}\n'
            r += f'\tscan output port: {scan_info.scan_out.name.str()}\n'
        return r

    def processDepth(self):
        self.processModuleDepth(self._top_module)
    
    def generatePorts(self):
        self.generateModulePorts()
    
    def CreateTopWrapper(self):
        top_module = self._top_module
        wires = list(top_module.wires_.values())
        input_ports = []
        input_bits = 0
        output_ports = []
        output_bits = 0
        clk_ports = []
        clk_bits = 0

        scan_ports = set()
        for clk in self.ModuleScanportInfo[top_module].scan_chains:
            scan_ports.add(self.ModuleScanportInfo[top_module].scan_chains[clk].scan_in)
            scan_ports.add(self.ModuleScanportInfo[top_module].scan_chains[clk].scan_out)
        scan_ports.add(self.ModuleScanportInfo[top_module].enable_port)

        for wire in wires:
            if wire.port_input:
                if wire in self.ModuleScanportInfo[top_module].scan_chains:
                    clk_ports.append(wire)
                    clk_bits += wire.width
                elif wire not in scan_ports:
                    input_ports.append(wire)
                    input_bits += wire.width
            if wire.port_output:
                if wire not in scan_ports:
                    output_ports.append(wire)
                    output_bits += wire.width
        top_wrapper = self._design.addModule(f"{top_module.name}_top_wrapper")
        scan_en_in = top_wrapper.addWire("\\scan_enable_in", 1)
        scan_en_in.port_input = True
        scan_in = top_wrapper.addWire("\\scan_in", clk_bits)
        scan_in.port_input = True
        scan_out = top_wrapper.addWire("\\scan_out", clk_bits)
        scan_out.port_output = True
        clk_in = top_wrapper.addWire("\\clk_in", clk_bits)
        clk_in.port_input = True
        dut_in = top_wrapper.addWire("\\dut_in", input_bits)
        dut_in.port_input = True
        dut_out = top_wrapper.addWire("\\dut_out", output_bits)
        dut_out.port_output = True
        top_wrapper.fixup_ports()

        dut_cell = top_wrapper.addCell("\\dut", top_module.name)
        dut_enable = self.ModuleScanportInfo[top_module].enable_port
        dut_cell.setPort(dut_enable.name, ys.SigSpec(scan_en_in))

        pos = 0
        for i, wire in enumerate(input_ports):
            dut_cell.setPort(wire.name, ys.SigSpec(ys.SigSpec(dut_in)[pos], wire.width))
            pos += wire.width
        pos = 0
        for i, wire in enumerate(output_ports):
            dut_cell.setPort(wire.name, ys.SigSpec(ys.SigSpec(dut_out)[pos], wire.width))
            pos += wire.width
        pos = 0
        for clk in self.ModuleScanportInfo[top_module].scan_chains:
            dut_cell.setPort(clk.name, ys.SigSpec(ys.SigSpec(clk_in)[pos], clk.width))
            pos += clk.width
        pos = 0
        for clk in self.ModuleScanportInfo[top_module].scan_chains:
            scan_info = self.ModuleScanportInfo[top_module].scan_chains[clk]
            dut_cell.setPort(scan_info.scan_in.name, ys.SigSpec(ys.SigSpec(scan_in)[pos], scan_info.scan_in.width))
            dut_cell.setPort(scan_info.scan_out.name, ys.SigSpec(ys.SigSpec(scan_out)[pos], scan_info.scan_out.width))
            pos += scan_info.scan_in.width
        
    def processTop(self):
        # First find sorting order of modules based on the depth on the instantiation tree.
        # depth 0 -> modules with no submodule instantiations.
        # depth 1 -> modules that instantiate only depth 0 modules.
        # etc
        # Then process modules in the order of increasing depth.
        # This way the submodules are always processed before the parent modules
        # and the clock configuration of the submodule can be trusted.
        #
        # The hierarchy is based on cell instantiations, but the contents of all submodules
        # is based only on the module definition.

        self.processDepth()
        self.processClocks()
        self.generatePorts()
        self.generateMuxes()
        self.CreateTopWrapper()

################
# Testing =>


design = ys.Design()

#test_name = "test_dffsr"
#test_name = "counter_8bit"
#test_name = "test_fsm"
test_name = "test_multiclock"

ys.run_pass(f"read_verilog -sv {test_name}.sv", design)
ys.run_pass(f"prep -top {test_name}", design)

ys.run_pass("proc", design)
ys.run_pass("opt_dff", design)

print("\n\n\n\nStaring analysis\n\n")

top_module = design.top_module()



test = TestClass(design, top_module)
test.processTop()

#top_module.check()
#ys.run_pass("check", design)
# ys.run_pass("opt")

ys.run_pass("write_rtlil out.rtlil", design)
ys.run_pass("write_verilog -sv -norename out.sv", design)

print("\n\n\n")

print("Scan chain info for top module:")
print(test.ScanInfo())

print("SCAN CHAIN ADDITION COMPLETED\n")

