import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

/// Change this to your backend's address.
/// - Android emulator: http://10.0.2.2:8000
/// - iOS simulator / physical device on same Wi-Fi: http://<your-computer-ip>:8000
const String kApiBaseUrl = 'http://10.0.2.2:8000';

class ApiService {
  static Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('token');
  }

  static Future<Map<String, String>> _authHeaders() async {
    final token = await _getToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  static Future<Map<String, dynamic>> login(String email, String password) async {
    final res = await http.post(
      Uri.parse('$kApiBaseUrl/auth/login'),
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: {'username': email, 'password': password},
    );
    if (res.statusCode != 200) {
      throw Exception(jsonDecode(res.body)['detail'] ?? 'Login failed');
    }
    final data = jsonDecode(res.body);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('token', data['access_token']);
    await prefs.setString('user', jsonEncode(data['user']));
    return data;
  }

  static Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('token');
    await prefs.remove('user');
  }

  static Future<Map<String, dynamic>?> currentUser() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString('user');
    return raw != null ? jsonDecode(raw) : null;
  }

  static Future<List<dynamic>> getAccounts() async {
    final res = await http.get(Uri.parse('$kApiBaseUrl/accounts/'), headers: await _authHeaders());
    return jsonDecode(res.body);
  }

  static Future<List<dynamic>> getTransactions() async {
    final res = await http.get(Uri.parse('$kApiBaseUrl/transactions/'), headers: await _authHeaders());
    return jsonDecode(res.body);
  }

  static Future<String> chat(String message, String language) async {
    final res = await http.post(
      Uri.parse('$kApiBaseUrl/assistant/chat'),
      headers: await _authHeaders(),
      body: jsonEncode({'message': message, 'language': language}),
    );
    final data = jsonDecode(res.body);
    return data['reply'] ?? '';
  }
}
