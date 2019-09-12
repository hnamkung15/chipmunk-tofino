from os import path

from antlr4 import CommonTokenStream
from antlr4 import FileStream
from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import StrictUndefined

from chipc.aluLexer import aluLexer
from chipc.aluParser import aluParser
from chipc.tofino_stateful_alu_visitor import TofinoStatefulAluVisitor
from chipc.tofino_stateless_alu_visitor import TofinoStatelessAluVisitor


class TofinoCodeGenerator:
    def __init__(self, sketch_name, num_alus_per_stage, num_pipeline_stages,
                 num_state_groups, constant_arr, stateful_alu_filename,
                 stateless_alu_filename, hole_assignments):
        self.sketch_name_ = sketch_name
        self.num_pipeline_stages_ = num_pipeline_stages
        self.num_alus_per_stage_ = num_alus_per_stage
        self.num_state_groups_ = num_state_groups
        self.constant_arr_ = constant_arr
        self.hole_assignments_ = hole_assignments
        self.stateful_alu_filename_ = stateful_alu_filename
        self.stateless_alu_filename_ = stateless_alu_filename

        self.jinja2_env_ = Environment(loader=FileSystemLoader(
            [path.join(path.dirname(__file__), './templates')]),
            undefined=StrictUndefined)

    def generate_alus(self):
        ret = ''
        stateful_alus = [[{}] * self.num_state_groups_
                         for i in range(self.num_pipeline_stages_)]
        stateless_alus = [[{}] * self.num_alus_per_stage_
                          for i in range(self.num_pipeline_stages_)]
        for i in range(self.num_pipeline_stages_):
            for j in range(self.num_alus_per_stage_):
                stateless_alu_template_dict = self.generate_stateless_alu(
                    'stateless_alu_' + str(i) + '_' + str(j))

                stateless_alus[i][j] = stateless_alu_template_dict
            for l in range(self.num_state_groups_):
                stateful_alu_template_dict = self.generate_stateful_alu(
                    'stateful_alu_' + str(i) + '_' + str(l))
                stateful_alu_template_dict['alu_name'] = 'salu_' + str(
                    i) + '_' + str(l)
                stateful_alu_template_dict['reg_name'] = 'reg_' + str(
                    i) + '_' + str(l)

                stateful_alus[i][l] = stateful_alu_template_dict

        print(stateless_alus)
        print(stateful_alus)
        return ret

    def generate_stateless_alu(self, alu_name):
        input_stream = FileStream(self.stateless_alu_filename_)
        lexer = aluLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = aluParser(stream)
        tree = parser.alu()

        tofino_stateless_alu_visitor = TofinoStatelessAluVisitor(
            self.stateless_alu_filename_, self.sketch_name_ + '_' + alu_name,
            self.constant_arr_, self.hole_assignments_)
        tofino_stateless_alu_visitor.visit(tree)

        return tofino_stateless_alu_visitor.template_args

    def generate_stateful_alu(self, alu_name):
        input_stream = FileStream(self.stateful_alu_filename_)
        lexer = aluLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = aluParser(stream)
        tree = parser.alu()

        tofino_stateful_alu_visitor = TofinoStatefulAluVisitor(
            self.sketch_name_ + '_' + alu_name, self.constant_arr_,
            self.hole_assignments_)
        tofino_stateful_alu_visitor.visit(tree)

        return tofino_stateful_alu_visitor.template_args

    def run(self):
        alu_definitions = self.generate_alus()

        print(alu_definitions)
