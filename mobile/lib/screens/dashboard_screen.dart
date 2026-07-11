import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'login_screen.dart';
import 'chat_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});
  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  List<dynamic> _accounts = [];
  List<dynamic> _transactions = [];
  Map<String, dynamic>? _user;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final user = await ApiService.currentUser();
    final accounts = await ApiService.getAccounts();
    final txns = await ApiService.getTransactions();
    setState(() {
      _user = user;
      _accounts = accounts;
      _transactions = txns;
      _loading = false;
    });
  }

  double get _totalBalance =>
      _accounts.fold(0.0, (sum, a) => sum + (a['balance'] as num).toDouble());

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F1B2B),
      appBar: AppBar(
        backgroundColor: const Color(0xFF16243A),
        title: Text(_user?['business_name'] ?? 'Dashboard', style: const TextStyle(color: Colors.white)),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout, color: Colors.white70),
            onPressed: () async {
              await ApiService.logout();
              if (!mounted) return;
              Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => const LoginScreen()));
            },
          )
        ],
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: const Color(0xFF2BB794),
        onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const ChatScreen())),
        child: const Icon(Icons.chat_bubble, color: Colors.black),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF2BB794)))
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: const Color(0xFF16243A),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: const Color(0xFF263954)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Total balance', style: TextStyle(color: Color(0xFF8A94A6), fontSize: 13)),
                        const SizedBox(height: 8),
                        Text('₹${_totalBalance.toStringAsFixed(2)}',
                            style: const TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                  const Text('Recent transactions', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600)),
                  const SizedBox(height: 10),
                  if (_transactions.isEmpty)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 20),
                      child: Text('No transactions yet.', style: TextStyle(color: Color(0xFF8A94A6))),
                    ),
                  ..._transactions.take(10).map((tx) => Container(
                        margin: const EdgeInsets.only(bottom: 8),
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: const Color(0xFF16243A),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: const Color(0xFF263954)),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(tx['type'].toString().replaceAll('_', ' '),
                                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500)),
                                Text(tx['category'], style: const TextStyle(color: Color(0xFF8A94A6), fontSize: 12)),
                              ],
                            ),
                            Text('₹${(tx['amount'] as num).toStringAsFixed(2)}',
                                style: const TextStyle(color: Color(0xFF2BB794), fontWeight: FontWeight.w600)),
                          ],
                        ),
                      )),
                ],
              ),
            ),
    );
  }
}
