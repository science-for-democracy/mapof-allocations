import os
from fractions import Fraction

from mapof.allocations.core.alloctask import AllocationTask, AllocationTaskLibrarian

class TestLibrarian:
  matrix = [
   [Fraction(1,10), Fraction(7,10), Fraction(2,10)],
   [Fraction(1,2), Fraction(3,10), Fraction(2,10)],
   [Fraction(0), Fraction(1,1), Fraction(0)],
   [Fraction(1,5), Fraction(2,5), Fraction(3,5)]
  ]
  correct_file_lines = [
         "4 3",
         "",
         "1/10 7/10 1/5",
         "1/2 3/10 1/5",
         "0 1 0",
         "1/5 2/5 3/5",
         "",
         "# 0.1\t0.7\t0.2",
         "# 0.5\t0.3\t0.2",
         "# 0.0\t1.0\t0.0",
         "# 0.2\t0.4\t0.6"
        ]

  def _save_test_matrix(self):
    alloc = AllocationTask.from_matrix(self.matrix, "test_id")
    librarian = AllocationTaskLibrarian()
    librarian.write(alloc, ".")


  def test_saving(self):
    try:
      self._save_test_matrix()
    finally:
      try:
        os.remove("test_id.alt")
      except:
          assert False, "Saving did not work properly"

  def test_saving_in_tree(self):
    nested_location = "test/directory/blah"
    try:
      alloc = AllocationTask.from_matrix(self.matrix, "test_id")
      librarian = AllocationTaskLibrarian()
      librarian.write(alloc, nested_location)
    finally:
      try:
        os.remove(os.path.join(nested_location,"test_id.alt"))
        os.removedirs(nested_location)
      except:
        assert False, "Saving did not work properly"


  def test_correct_content_saving(self):
    try:
      self._save_test_matrix()
      with open("test_id.alt", "r") as ffile: 
        for i, line in enumerate(ffile):
          print(line)
          assert self.correct_file_lines[i] == line.strip(), f"Line {i+1} contains an incorrect content"
    except Exception as e:
      assert False, f"Saving did not work properly: {e}"
    finally:
      try:
        os.remove("test_id.alt")
      except:
        pass

  def test_correct_reading(self):
    try:
      with open("test_id.alt", "w") as ffile: 
        for line in self.correct_file_lines:
          ffile.write(f"{line}\n")
      librarian = AllocationTaskLibrarian()
      alloc = librarian.read("test_id.alt")
      print(alloc)
      assert alloc == self.matrix
    finally:
      try:
        os.remove("test_id.alt")
      except:
        pass



