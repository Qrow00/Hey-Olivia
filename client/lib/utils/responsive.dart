import 'package:flutter/material.dart';

class Display {
  static bool isPhone(BuildContext c) => MediaQuery.of(c).size.shortestSide < 600;
  static bool isTablet(BuildContext c) => MediaQuery.of(c).size.shortestSide >= 600;
  static bool isLandscape(BuildContext c) => MediaQuery.of(c).orientation == Orientation.landscape;

  static double drawerWidth(BuildContext c) => isPhone(c) ? 280 : 360;
  static double cardGap(BuildContext c) => isPhone(c) ? 10 : 16;
  static EdgeInsets padding(BuildContext c) => EdgeInsets.all(isPhone(c) ? 16 : 24);
  static EdgeInsets cardPadding(BuildContext c) => EdgeInsets.all(isPhone(c) ? 14 : 20);

  static int gridColumns(BuildContext c) => isPhone(c) ? 1 : 2;
}
