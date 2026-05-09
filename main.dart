import 'package:flutter/material.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Altyapi Test',
      theme: ThemeData.dark(),
      home: const Scaffold(
        body: Center(
          child: Text(
            'Altyapı Kurulumu Başarılı!',
            style: TextStyle(fontSize: 24, color: Colors.greenAccent),
          ),
        ),
      ),
    );
  }
}