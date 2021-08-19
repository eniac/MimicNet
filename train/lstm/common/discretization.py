def calc_index(v, base, step):
    return int((v-base)/step)

def retrieve_value(ind, base, step):
    return base + ind*step


def discretize(ts, granu):
    vmin = vmax = ts[0] 
    for i in ts:
        if i == 100: ## filter losses
            continue
        if i > vmax:
            vmax = i
        elif i < vmin:
            vmin = i

    print("DIS_MIN=", vmin)
    print("DIS_MAX=", vmax)

    step = (vmax - vmin) / granu
    res = []
    for i in ts:
        res.append(calc_index(i, vmin, step))

    return res, (vmin, step)

def recover_real(ts, meta):
    res = []
    for i in ts:
        res.append(retrieve_value(i, meta[0], meta[1]))
    return res
