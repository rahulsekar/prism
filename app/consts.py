class ProdType(object):
    index = 0
    idx_fut = 1
    idx_opt = 2
    equity = 3
    eq_fut = 4
    eq_opt = 5
    g_sec = 6
    t_bill = 7
    max_type = 100

class OptType(object):
    NA = 0
    CE = 1 #call european
    PE = 2 #put european
    CA = 3 #call american
    PA = 4 #put american

class CouponFreq(object):
    zero = 0
    yearly = 1
    half_yearly = 2
