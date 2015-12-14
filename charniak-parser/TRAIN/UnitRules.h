/*
 * Copyright 2005 Brown University, Providence, RI.
 * 
 *                         All Rights Reserved
 * 
 * Permission to use, copy, modify, and distribute this software and its
 * documentation for any purpose other than its incorporation into a
 * commercial product is hereby granted without fee, provided that the
 * above copyright notice appear in all copies and that both that
 * copyright notice and this permission notice appear in supporting
 * documentation, and that the name of Brown University not be used in
 * advertising or publicity pertaining to distribution of the software
 * without specific, written prior permission.
 * 
 * BROWN UNIVERSITY DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
 * INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR ANY
 * PARTICULAR PURPOSE.  IN NO EVENT SHALL BROWN UNIVERSITY BE LIABLE FOR
 * ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 */

#ifndef UNITRULES_H
#define UNITRULES_H

#include "InputTree.h"
#include <iostream>
#include <fstream>
#include "Feature.h"

class UnitRules
{
 public:
  void init();
  void readTrees(istream& dataStream);
  void gatherData(InputTree* tree);
  void setData(ECString path);
  bool badPair(int par, int chi);
  void readData(ECString path);
  int& treeData(int i, int j) { return treeData_[i][j]; }
  int treeData(int i, int j) const { return treeData_[i][j]; }
 private:
  int numRules_;
  int unitRules[MAXNUMNTS];
  int treeData_[MAXNUMNTS][MAXNUMNTS];
  bool before_;
};

#endif /*UNITRULES_H */
