<?php
namespace PHPMailer\PHPMailer;

class SMTP
{
    public $do_debug = 0;
    public $Debugoutput = 'echo';
    public $Timeout = 300;
    public $Timelimit = 300;
    
    private $smtp_conn = null;
    private $error = [
        'error' => '',
        'detail' => '',
        'smtp_code' => '',
        'smtp_code_ex' => ''
    ];
    
    public function connect($host, $port = 25, $timeout = 30, $options = [])
    {
        $this->error = ['error' => '', 'detail' => '', 'smtp_code' => '', 'smtp_code_ex' => ''];
        
        set_error_handler([$this, 'errorHandler']);
        $this->smtp_conn = fsockopen(
            $host,
            $port,
            $errno,
            $errstr,
            $timeout
        );
        restore_error_handler();
        
        if (!is_resource($this->smtp_conn)) {
            $this->error = [
                'error' => 'Failed to connect to server',
                'detail' => $errstr,
                'smtp_code' => (string)$errno,
                'smtp_code_ex' => ''
            ];
            return false;
        }
        
        stream_set_timeout($this->smtp_conn, $this->Timeout, 0);
        $announce = $this->get_lines();
        
        if (substr($announce, 0, 3) != '220') {
            $this->error = [
                'error' => 'SMTP server not ready',
                'detail' => $announce,
                'smtp_code' => substr($announce, 0, 3),
                'smtp_code_ex' => ''
            ];
            fclose($this->smtp_conn);
            $this->smtp_conn = null;
            return false;
        }
        
        return true;
    }
    
    public function hello($host = '')
    {
        return $this->sendCommand('HELO', 'HELO ' . $host, 250);
    }
    
    public function authenticate($username, $password, $authtype = null, $OAuth = null)
    {
        if (!$this->sendCommand('AUTH LOGIN', 'AUTH LOGIN', 334)) {
            return false;
        }
        if (!$this->sendCommand('Username', base64_encode($username), 334)) {
            return false;
        }
        if (!$this->sendCommand('Password', base64_encode($password), 235)) {
            return false;
        }
        return true;
    }
    
    public function send($header, $body)
    {
        if (!$this->sendCommand('MAIL', 'MAIL FROM:<' . $this->mail->From . '>', 250)) {
            return false;
        }
        if (!$this->sendCommand('RCPT', 'RCPT TO:<' . $this->mail->recipient . '>', 250)) {
            return false;
        }
        if (!$this->sendCommand('DATA', 'DATA', 354)) {
            return false;
        }
        $this->client_send($header . $body);
        return $this->sendCommand('DATA END', '.', 250);
    }
    
    public function startTLS()
    {
        if (!$this->sendCommand('STARTTLS', 'STARTTLS', 220)) {
            return false;
        }
        if (!stream_socket_enable_crypto(
            $this->smtp_conn,
            true,
            STREAM_CRYPTO_METHOD_TLS_CLIENT
        )) {
            return false;
        }
        return true;
    }
    
    public function quit()
    {
        $this->sendCommand('QUIT', 'QUIT', 221);
        $this->close();
    }
    
    public function close()
    {
        if (is_resource($this->smtp_conn)) {
            fclose($this->smtp_conn);
            $this->smtp_conn = null;
        }
    }
    
    public function connected()
    {
        if (is_resource($this->smtp_conn)) {
            $sock_status = stream_get_meta_data($this->smtp_conn);
            if ($sock_status['eof']) {
                $this->close();
                return false;
            }
            return true;
        }
        return false;
    }
    
    private function sendCommand($command, $commandstring, $expect)
    {
        if (!$this->connected()) {
            $this->error = ['error' => 'Called ' . $command . ' without being connected'];
            return false;
        }
        
        $this->client_send($commandstring . "\r\n", $command);
        $this->last_reply = $this->get_lines();
        
        $code = substr($this->last_reply, 0, 3);
        if (!in_array($code, (array)$expect)) {
            $this->error = [
                'error' => $command . ' command failed',
                'detail' => $this->last_reply,
                'smtp_code' => $code,
                'smtp_code_ex' => ''
            ];
            return false;
        }
        
        $this->error = ['error' => ''];
        return true;
    }
    
    private function client_send($data, $command = '')
    {
        fwrite($this->smtp_conn, $data);
    }
    
    private function get_lines()
    {
        $data = '';
        $endtime = 0;
        
        if ($this->Timelimit > 0) {
            $endtime = time() + $this->Timelimit;
        }
        
        while (is_resource($this->smtp_conn) && !feof($this->smtp_conn)) {
            $str = fgets($this->smtp_conn, 515);
            $data .= $str;
            
            if (substr($str, 3, 1) == ' ') {
                break;
            }
            
            $info = stream_get_meta_data($this->smtp_conn);
            if ($info['timed_out']) {
                break;
            }
            
            if ($endtime && time() > $endtime) {
                break;
            }
        }
        
        return $data;
    }
    
    private function errorHandler($errno, $errmsg, $errfile = '', $errline = 0)
    {
        $notice = 'Connection failed.';
        $this->error = [
            'error' => $notice,
            'detail' => $errmsg,
            'smtp_code' => (string)$errno,
            'smtp_code_ex' => ''
        ];
    }
    
    public function setVerp($enabled = false)
    {
        $this->do_verp = $enabled;
    }
    
    public function setDebugLevel($level = 0)
    {
        $this->do_debug = $level;
    }
    
    public function setDebugOutput($method = 'echo')
    {
        $this->Debugoutput = $method;
    }
    
    public function setTimeout($timeout = 0)
    {
        $this->Timeout = $timeout;
    }
}