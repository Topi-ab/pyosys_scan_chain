from pyosys import libyosys as ys

design = ys.Design()

#test_name = "test_dffsr"
test_name = "counter_8bit"

ys.run_pass(f"read_verilog -sv {test_name}.sv", design)
ys.run_pass(f"prep -top {test_name}", design)

ys.run_pass("proc", design)
ys.run_pass("opt_dff", design)

print("\n\n\n\nStaring analysis\n\n")

top_module = design.top_module()

def fresh_id() -> ys.IdString:
    r = ys.IdString.new_autoidx_with_prefix("$auto$")
    return r

class TestClass:
    def __init__(self, design: ys.Design):
        self._modules_ports = []
        self._module_muxes = []
        self._design = design

    def AddScanPorts(self, module: ys.Module):
        en_port = module.addWire("\\scan_enable_in")
        en_port.port_input = True

        scan_in_port = module.addWire("\\scan_in")
        scan_in_port.port_input = True

        scan_out_port = module.addWire("\\scan_out")
        scan_out_port.port_output = True

        module.fixup_ports()

    def AddMuxes(self, module: ys.Module) -> int:
        dff_cnt = 0
        en_port = ys.SigSpec(module.wire("\\scan_enable_in"))
        scan_in_port = ys.SigSpec(module.wire("\\scan_in"))
        scan_out_port = ys.SigSpec(module.wire("\\scan_out"))

        dff_set = set()
        cells = list(module.cells_.values())
        for cell in cells:
            # TODO: detect also $fsm.
            # TODO: Separate mechanism for memories.
            # TODO: Clock polarity.

            # DFF types:
            # $sr $ff $dff $dffe $adff $adffe $aldff $aldffe $sdff $sdffe $sdffce $dffsr $dffsre $dlatch $adlatch $dlatchsr
            
            # DFF ports:
            # CLK, D, Q, EN, SET, CLR, ARST, ALOAD, AD, SRST
            
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
                        mux = module.addMux(fresh_id(), ys.SigSpec(orig_d), ys.SigSpec(new_d), en_port, ys.SigSpec(mux_y), "scan chain data mux")
                        cell.setPort("\\D", ys.SigSpec(mux_y))
                        dff_set.add((new_d, orig_q, width))
                    case _:
                        raise Exception(f'"Unsupported flip-flop type: {type}"')
            elif cell.type in self._design.modules_:
                s_in = module.addWire(fresh_id(), 1)
                s_out = module.addWire(fresh_id(), 1)

                cell.setPort("\\scan_enable_in", en_port)
                cell.setPort("\\scan_in", ys.SigSpec(s_in))
                cell.setPort("\\scan_out", ys.SigSpec(s_out))
                dff_set.add((s_in, s_out, 0))

        scan_in = scan_in_port
        for new_d, orig_q, cnt in dff_set:
            dff_cnt += cnt
            for i in range(new_d.width):
                a = scan_in
                b = ys.SigSpec(new_d)[i]
                c = ys.SigSpec(b, 1)
                module.connect(c, a)
                d = ys.SigSpec(orig_q)[i]
                e = ys.SigSpec(d, 1)
                scan_in = e
        module.connect(scan_out_port, scan_in)
        return dff_cnt

    def processModulePorts(self, module: ys.Module):
        if module not in self._modules_ports:
            self._modules_ports.append(module)
            print(f'Adding ports to module: {module.name.str()}')
            self.AddScanPorts(module)
            cells = list(module.cells_.values())
            for cell in cells:
                if cell.type in self._design.modules_:
                    submod = self._design.modules_[cell.type]
                    self.processModulePorts(submod)

    def processModuleMuxes(self, module: ys.Module) -> int:
        dff_cnt = 0
        if module not in self._module_muxes:
            self._module_muxes.append(module)
            print(f'Adding muxes to module: {module.name.str()}')
            dff_cnt += self.AddMuxes(module)
            cells = list(module.cells_.values())
            for cell in cells:
                if cell.type in self._design.modules_:
                    submod = self._design.modules_[cell.type]
                    dff_cnt += self.processModuleMuxes(submod)
        return dff_cnt



test = TestClass(design)
test.processModulePorts(top_module)
dff_cnt = test.processModuleMuxes(top_module)

#top_module.check()

#ys.run_pass("check", design)

# ys.run_pass("opt")

ys.run_pass("write_rtlil out.rtlil", design)
ys.run_pass("write_verilog -sv out.sv", design)

#ys.run_pass("dump", design)

print("\n\n\n")
print(f'Total DFFs processed: {dff_cnt}')
print("SCAN CHAIN ADDITION COMPLETED\n")

