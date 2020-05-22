import tempfile
import unittest
import os
import shutil

import numpy as np

from deepchem.utils import rdkit_util


class TestRdkitUtil(unittest.TestCase):

  def setUp(self):
    # TODO test more formats for ligand
    current_dir = os.path.dirname(os.path.realpath(__file__))
    self.protein_file = os.path.join(
        current_dir, '../../feat/tests/3ws9_protein_fixer_rdkit.pdb')
    self.ligand_file = os.path.join(current_dir,
                                    '../../feat/tests/3ws9_ligand.sdf')

  def test_load_complex(self):
    pass

  def test_load_molecule(self):
    # adding hydrogens and charges is tested in dc.utils
    from rdkit.Chem.AllChem import Mol
    for add_hydrogens in (True, False):
      for calc_charges in (True, False):
        mol_xyz, mol_rdk = rdkit_util.load_molecule(self.ligand_file,
                                                    add_hydrogens, calc_charges)
        num_atoms = mol_rdk.GetNumAtoms()
        self.assertIsInstance(mol_xyz, np.ndarray)
        self.assertIsInstance(mol_rdk, Mol)
        self.assertEqual(mol_xyz.shape, (num_atoms, 3))

  def test_get_xyz_from_mol(self):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    ligand_file = os.path.join(current_dir, "../../dock/tests/1jld_ligand.sdf")

    xyz, mol = rdkit_util.load_molecule(
        ligand_file, calc_charges=False, add_hydrogens=False)
    xyz2 = rdkit_util.get_xyz_from_mol(mol)

    equal_array = np.all(xyz == xyz2)
    assert equal_array

  def test_add_hydrogens_to_mol(self):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    ligand_file = os.path.join(current_dir, "../../dock/tests/1jld_ligand.sdf")
    xyz, mol = rdkit_util.load_molecule(
        ligand_file, calc_charges=False, add_hydrogens=False)
    original_hydrogen_count = 0
    for atom_idx in range(mol.GetNumAtoms()):
      atom = mol.GetAtoms()[atom_idx]
      if atom.GetAtomicNum() == 1:
        original_hydrogen_count += 1

    assert mol is not None
    mol = rdkit_util.add_hydrogens_to_mol(mol, is_protein=False)
    assert mol is not None
    after_hydrogen_count = 0
    for atom_idx in range(mol.GetNumAtoms()):
      atom = mol.GetAtoms()[atom_idx]
      if atom.GetAtomicNum() == 1:
        after_hydrogen_count += 1
    assert after_hydrogen_count >= original_hydrogen_count

  def test_apply_pdbfixer(self):
    pass

  def test_compute_charges(self):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    ligand_file = os.path.join(current_dir, "../../dock/tests/1jld_ligand.sdf")
    xyz, mol = rdkit_util.load_molecule(
        ligand_file, calc_charges=False, add_hydrogens=True)
    rdkit_util.compute_charges(mol)

    has_a_charge = False
    for atom_idx in range(mol.GetNumAtoms()):
      atom = mol.GetAtoms()[atom_idx]
      value = atom.GetProp(str("_GasteigerCharge"))
      if value != 0:
        has_a_charge = True
    assert has_a_charge

  def test_rotate_molecules(self):
    # check if distances do not change
    vectors = np.random.rand(4, 2, 3)
    norms = np.linalg.norm(vectors[:, 1] - vectors[:, 0], axis=1)
    vectors_rot = np.array(rdkit_util.rotate_molecules(vectors))
    norms_rot = np.linalg.norm(vectors_rot[:, 1] - vectors_rot[:, 0], axis=1)
    self.assertTrue(np.allclose(norms, norms_rot))

    # check if it works for molecules with different numbers of atoms
    coords = [np.random.rand(n, 3) for n in (10, 20, 40, 100)]
    coords_rot = rdkit_util.rotate_molecules(coords)
    self.assertEqual(len(coords), len(coords_rot))

  def test_load_molecule(self):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    ligand_file = os.path.join(current_dir, "../../dock/tests/1jld_ligand.sdf")
    xyz, mol = rdkit_util.load_molecule(
        ligand_file, calc_charges=False, add_hydrogens=False)
    assert xyz is not None
    assert mol is not None

  def test_write_molecule(self):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    ligand_file = os.path.join(current_dir, "../../dock/tests/1jld_ligand.sdf")
    xyz, mol = rdkit_util.load_molecule(
        ligand_file, calc_charges=False, add_hydrogens=False)

    with tempfile.TemporaryDirectory() as tmp:
      outfile = os.path.join(tmp, "mol.sdf")
      rdkit_util.write_molecule(mol, outfile)

      xyz, mol2 = rdkit_util.load_molecule(
          outfile, calc_charges=False, add_hydrogens=False)

    assert mol.GetNumAtoms() == mol2.GetNumAtoms()
    for atom_idx in range(mol.GetNumAtoms()):
      atom1 = mol.GetAtoms()[atom_idx]
      atom2 = mol.GetAtoms()[atom_idx]
      assert atom1.GetAtomicNum() == atom2.GetAtomicNum()

  def test_pdbqt_to_pdb(self):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    protein_file = os.path.join(current_dir,
                                "../../dock/tests/1jld_protein.pdb")
    xyz, mol = rdkit_util.load_molecule(
        protein_file, calc_charges=False, add_hydrogens=False)
    with tempfile.TemporaryDirectory() as tmp:
      out_pdb = os.path.join(tmp, "mol.pdb")
      out_pdbqt = os.path.join(tmp, "mol.pdbqt")

      rdkit_util.write_molecule(mol, out_pdb)
      rdkit_util.write_molecule(mol, out_pdbqt, is_protein=True)

      pdb_block = rdkit_util.pdbqt_to_pdb(out_pdbqt)
      from rdkit import Chem
      pdb_mol = Chem.MolFromPDBBlock(pdb_block, sanitize=False, removeHs=False)

      xyz, pdbqt_mol = rdkit_util.load_molecule(
          out_pdbqt, add_hydrogens=False, calc_charges=False)

    assert pdb_mol.GetNumAtoms() == pdbqt_mol.GetNumAtoms()
    for atom_idx in range(pdb_mol.GetNumAtoms()):
      atom1 = pdb_mol.GetAtoms()[atom_idx]
      atom2 = pdbqt_mol.GetAtoms()[atom_idx]
      assert atom1.GetAtomicNum() == atom2.GetAtomicNum()

  def test_merge_molecules_xyz(self):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    ligand_file = os.path.join(current_dir, "../../dock/tests/1jld_ligand.sdf")
    xyz, mol = rdkit_util.load_molecule(
        ligand_file, calc_charges=False, add_hydrogens=False)
    merged = rdkit_util.merge_molecules_xyz([xyz, xyz])
    for i in range(len(xyz)):
      first_atom_equal = np.all(xyz[i] == merged[i])
      second_atom_equal = np.all(xyz[i] == merged[i + len(xyz)])
      assert first_atom_equal
      assert second_atom_equal
