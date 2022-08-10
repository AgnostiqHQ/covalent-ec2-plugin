# Copyright 2021 Agnostiq Inc.
#
# This file is part of Covalent.
#
# Licensed under the GNU Affero General Public License 3.0 (the "License").
# A copy of the License may be obtained with this software package or at
#
#      https://www.gnu.org/licenses/agpl-3.0.en.html
#
# Use of this file is prohibited except in compliance with the License. Any
# modifications or derivative works of this file must retain this copyright
# notice, and modified files must contain a notice indicating that they have
# been altered from the originals.
#
# Covalent is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the License for more details.
#
# Relief from the License may be granted by purchasing a commercial license.


EXEC_SCRIPT = """
import sys

result = None
exception = None

try:
    import cloudpickle as pickle
except Exception as e:
    import pickle

with open('{remote_result_file}', 'wb') as f_out:
    pickle.dump((None, e), f_out)
    exit()

with open('{remote_function_file}', 'rb') as f_in:
    fn, args, kwargs = pickle.load(f_in)
    try:
        result = fn(*args, **kwargs)
    except Exception as e:
        exception = f' The function is {fn} and its Exception occured at line 387 with status {e}

with open('{remote_result_file}','wb') as f_out:
    pickle.dump((result, exception), f_out)
"""
