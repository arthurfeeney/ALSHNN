

import sys
sys.path.append('../LSH/')

import torch
from LSH.tables_cpu import TablesCPU
from LSH.tables_gpu import TablesGPU

class ALSHConv:
    def init_ALSH(self, num_tables, table_size, which_hash, hash_init_params,
                  num_hashes, dim, num_filters, device):
        assert isinstance(device, str), 'ALSHConv, device must be a string'
        assert device == 'cpu' or device == 'gpu', \
            'ALSHConv, device must be a \'cpu\' or \'gpu\'.'
        
        #if device == 'cpu':
        self.tables = TablesCPU(num_tables, table_size, which_hash, 
                                    hash_init_params, num_hashes, dim)
        #if device == 'gpu':
        #self.tables = TablesGPU(num_tables, table_size, which_hash, 
        #                            hash_init_params, num_hashes, dim, 
        #                            num_filters)

    def fill_table(self, filters):
        num = filters.size(0)
        self.tables.insert_data(filters.view(num, -1), range(num))

    def refill(self, active_kernels, active_set, table_indices):
        self.tables.clear_row(table_indices)

        num = active_kernels.size(0)

        self.tables.insert_data(active_kernels.view(num, -1), active_set)  

    def most_freq(self, x, k=5):
        bins = self.tables.table_size
        item_freq = torch.histc(x, bins=bins, max=bins)
        return item_freq.topk(k)[1]
    
    def get_active_set(self, input, kernel_size, stride, padding, dilation):

        ti = self.tables.get(input, kernel_size=kernel_size, 
                             stride=stride,  padding=padding, 
                             dilation=dilation)

        topkl = torch.zeros(ti.size(0), 5).long()
        for row in range(ti.size(0)):
            topkl[row] = self.most_freq(ti[row], k=5)


        # accessing tables directly should be faster and safe because 
        # it will do a copy when creating tensor
        
        #AS = torch.cat([torch.Tensor(self.tables.tables[i][ti[i]]).long() for i in range(self.tables.num_tables)]).unique()

        AS = torch.Tensor([]).long()
        for i in range(self.tables.num_tables):
            for j in topkl[i]:
                AS = torch.cat((AS, torch.Tensor(self.tables.tables[i][j]).long()))

        #AS = torch.zeros(self.tables.num_filters).byte()
        #for i in range(self.tables.num_tables):
        #    AS = AS | self.tables.tables[i][ti[i]]

        return AS, ti
        
