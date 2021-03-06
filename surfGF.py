import numpy as np
import numpy.linalg as LA
from inputGF import *
import iteration





def construct_H00_H01(g, kpt):
    principle_layer_thickness = g.dict['principle_layer_thickness']
    surface_index = g.dict['slab_direction']

    plane_dist = []  # plane distance to the plane which crosses (0, 0, 0)
    for i in range(g.nrpt):
        plane_dist.append(
            surface_index[0] * g.rpt[i, 0] + surface_index[1] * g.rpt[i, 1] + surface_index[2] * g.rpt[i, 2])

    max_dist = max(plane_dist)
    min_dist = min(plane_dist)

    atom_layer = []
    atom_layer1 = []
    for i in range(2 * principle_layer_thickness - 1):
        j = i - principle_layer_thickness + 1
        if j <= max_dist and j >= min_dist:
            atom_layer.append([k for k, x in enumerate(plane_dist) if x == j])
        else:
            atom_layer.append('None')
        if i + 1 <= max_dist:
            atom_layer1.append([k for k, x in enumerate(plane_dist) if x == i + 1])
        else:
            atom_layer1.append('None')
    '''
    print(g.rpt)
    print(atom_layer)
    print(atom_layer1)
    '''

    H00 = np.zeros((principle_layer_thickness * g.num_wann, principle_layer_thickness * g.num_wann), dtype=np.complex)
    H01 = np.zeros((principle_layer_thickness * g.num_wann, principle_layer_thickness * g.num_wann), dtype=np.complex)
    for i in range(principle_layer_thickness):
        for j in range(principle_layer_thickness):
            hamij = np.zeros((g.num_wann, g.num_wann), dtype=np.complex)
            hamij1 = np.zeros((g.num_wann, g.num_wann), dtype=np.complex)
            num_atom_layer = j - i + principle_layer_thickness - 1  # number between j and i
            num_atom_layer1 = num_atom_layer

            if atom_layer[num_atom_layer] != 'None':
                for k in atom_layer[num_atom_layer]:
                    hamij += np.exp(1j * np.dot(g.point_scale(kpt, g.b), g.point_scale(g.rpt[k], g.a))) * (
                        g.hamr[:, :, k] + 1j * g.hami[:, :, k])  # *g.weight[k]
            H00[g.num_wann * i:g.num_wann * (i + 1), g.num_wann * j:g.num_wann * (j + 1)] = hamij

            if atom_layer1[num_atom_layer1] != 'None':
                for k1 in atom_layer1[num_atom_layer1]:
                    hamij1 += np.exp(1j * np.dot(g.point_scale(kpt, g.b), g.point_scale(g.rpt[k1], g.a))) * (
                        g.hamr[:, :, k1] + 1j * g.hami[:, :, k1])  # *g.weight[k]
            H01[g.num_wann * i:g.num_wann * (i + 1), g.num_wann * j:g.num_wann * (j + 1)] = hamij1

    return H00, H01


def per_k(g, kpt):
    H00, H01 = construct_H00_H01(g, kpt)
    epsilon0 = H00
    alpha0 = H01
    beta0 = H01.conj().T
    max_step = g.dict['maximum_iteration']
    smearing = g.dict['smearing']
    prec = g.dict['convergence']
    num_wann = g.num_wann
    g00_list = iteration.iteration.iterate_k(alpha0, beta0, epsilon0, epsilon0, g.eng_list, smearing, prec,
                                             max_step)  # array
    surf_spectral = -1.0 / np.pi * np.imag(np.trace(g00_list[0:num_wann, 0:num_wann, :]))

    # surface potential modified
    a, b, c = np.shape(g00_list)
    g00_modified_list = np.zeros((a, b, c), dtype='complex')
    V = g.dict['surface_potential']
    surf_spectral_modified = np.zeros((c,))
    if V != None and V != 0:
        eye_matrix = np.eye(a, dtype='complex')
        for i in range(c):
            temp = LA.inv((g.eng_list[i] + 1j * smearing - V) * eye_matrix
                          - H00 - np.dot(alpha0, np.dot(g00_list[:, :, i], beta0)))
            g00_modified_list[:, :, i] = temp
        surf_spectral_modified = -1.0 / np.pi * np.imag(np.trace(g00_modified_list[0:num_wann, 0:num_wann, :]))

    return surf_spectral, surf_spectral_modified
