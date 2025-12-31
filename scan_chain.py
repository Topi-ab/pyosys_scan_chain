from pyosys import libyosys as ys

design = ys.Design()

ys.run_pass("read_verilog -sv counter_8bit.sv", design)
ys.run_pass("prep -top counter_8bit", design)
ys.run_pass("proc", design)

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
        en_port = module.wire("\\scan_enable_in")
        scan_in_port = module.wire("\\scan_in")
        scan_out_port = module.wire("\\scan_out")

        dff_set = set()
        cells = list(module.cells_.values())
        for cell in cells:
            if cell.type.str() in ["$dff"]:
                orig_d = cell.getPort("\\D")
                orig_q = cell.getPort("\\Q")
                width = orig_d.size()

                new_d = module.addWire(fresh_id(), width)
                mux_y = module.addWire(fresh_id(), width)
                mux = module.addMux(fresh_id(), ys.SigSpec(orig_d), ys.SigSpec(new_d), ys.SigSpec(en_port), ys.SigSpec(mux_y), "asdfa")
                cell.setPort("\\D", ys.SigSpec(mux_y))
                dff_set.add((new_d, orig_q, width))
            if cell.type in self._design.modules_:
                s_in = module.addWire(fresh_id(), 1)
                s_out = module.addWire(fresh_id(), 1)

                cell.setPort("\\scan_enable_in", ys.SigSpec(en_port))
                cell.setPort("\\scan_in", ys.SigSpec(s_in))
                cell.setPort("\\scan_out", ys.SigSpec(s_out))
                dff_set.add((s_in, s_out, 0))

        scan_in = ys.SigSpec(scan_in_port)
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
        module.connect(ys.SigSpec(scan_out_port), scan_in)
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
print(f'Total DFFs processed: {dff_cnt}')

#top_module.check()

#ys.run_pass("check", design)

ys.run_pass("write_rtlil out.rtlil", design)
ys.run_pass("write_verilog -sv out.sv", design)

#ys.run_pass("dump", design)

pass
