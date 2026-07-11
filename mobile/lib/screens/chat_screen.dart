import 'package:flutter/material.dart';
import '../services/api_service.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});
  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final List<Map<String, String>> _messages = [
    {'role': 'assistant', 'content': 'Hi! Ask me about your balance, spending, or recent transactions.'}
  ];
  final _controller = TextEditingController();
  String _language = 'en';
  bool _loading = false;

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    setState(() {
      _messages.add({'role': 'user', 'content': text});
      _loading = true;
      _controller.clear();
    });
    try {
      final reply = await ApiService.chat(text, _language);
      setState(() => _messages.add({'role': 'assistant', 'content': reply}));
    } catch (e) {
      setState(() => _messages.add({'role': 'assistant', 'content': "Sorry, I couldn't reach the assistant."}));
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F1B2B),
      appBar: AppBar(
        backgroundColor: const Color(0xFF16243A),
        title: const Text('Banking Assistant', style: TextStyle(color: Colors.white)),
        actions: [
          DropdownButton<String>(
            value: _language,
            dropdownColor: const Color(0xFF16243A),
            underline: const SizedBox(),
            items: const [
              DropdownMenuItem(value: 'en', child: Text('EN', style: TextStyle(color: Colors.white))),
              DropdownMenuItem(value: 'hi', child: Text('हिं', style: TextStyle(color: Colors.white))),
              DropdownMenuItem(value: 'te', child: Text('తె', style: TextStyle(color: Colors.white))),
            ],
            onChanged: (v) => setState(() => _language = v ?? 'en'),
          ),
          const SizedBox(width: 12),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length + (_loading ? 1 : 0),
              itemBuilder: (context, i) {
                if (i >= _messages.length) {
                  return _bubble('Thinking…', isUser: false);
                }
                final m = _messages[i];
                return _bubble(m['content']!, isUser: m['role'] == 'user');
              },
            ),
          ),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: const BoxDecoration(
              color: Color(0xFF16243A),
              border: Border(top: BorderSide(color: Color(0xFF263954))),
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    style: const TextStyle(color: Colors.white),
                    decoration: InputDecoration(
                      hintText: 'Ask about balance, spending...',
                      hintStyle: const TextStyle(color: Color(0xFF8A94A6)),
                      filled: true,
                      fillColor: const Color(0xFF1C2E48),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(20), borderSide: BorderSide.none),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                    ),
                    onSubmitted: (_) => _send(),
                  ),
                ),
                const SizedBox(width: 8),
                CircleAvatar(
                  backgroundColor: const Color(0xFF2BB794),
                  child: IconButton(icon: const Icon(Icons.send, color: Colors.black, size: 18), onPressed: _send),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _bubble(String text, {required bool isUser}) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
        decoration: BoxDecoration(
          color: isUser ? const Color(0xFF2BB794) : const Color(0xFF1C2E48),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Text(text, style: TextStyle(color: isUser ? Colors.black : Colors.white, fontSize: 13)),
      ),
    );
  }
}
