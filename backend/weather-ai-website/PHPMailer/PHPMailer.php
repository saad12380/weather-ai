<?php
namespace PHPMailer\PHPMailer;

class PHPMailer
{
    public $CharSet = 'UTF-8';
    public $ContentType = 'text/plain';
    public $Encoding = '8bit';
    public $ErrorInfo = '';
    public $From = '';
    public $FromName = '';
    public $Sender = '';
    public $Subject = '';
    public $Body = '';
    public $AltBody = '';
    public $isHTML = false;
    public $Host = 'localhost';
    public $Port = 25;
    public $SMTPSecure = '';
    public $SMTPAuth = false;
    public $Username = '';
    public $Password = '';
    public $Timeout = 300;
    public $SMTPDebug = 0;
    public $Debugoutput = 'echo';
    public $do_verp = false;
    public $SMTPKeepAlive = false;
    
    private $smtp = null;
    private $exceptions = false;
    
    public function __construct($exceptions = false)
    {
        $this->exceptions = (bool)$exceptions;
    }
    
    public function isSMTP()
    {
        $this->Mailer = 'smtp';
    }
    
    public function isHTML($isHtml = true)
    {
        $this->isHTML = (bool)$isHtml;
        if ($isHtml) {
            $this->ContentType = 'text/html';
        }
    }
    
    public function send()
    {
        try {
            if (!$this->preSend()) {
                return false;
            }
            return $this->postSend();
        } catch (Exception $e) {
            $this->mailHeader = '';
            $this->ErrorInfo = $e->getMessage();
            if ($this->exceptions) {
                throw $e;
            }
            return false;
        }
    }
    
    private function preSend()
    {
        if (empty($this->From)) {
            throw new Exception('From address is not set');
        }
        return true;
    }
    
    private function postSend()
    {
        try {
            $this->smtpConnect();
            $this->smtp->send($this->createHeader(), $this->Body);
            $this->smtpClose();
            return true;
        } catch (Exception $e) {
            $this->ErrorInfo = $e->getMessage();
            if ($this->exceptions) {
                throw $e;
            }
            return false;
        }
    }
    
    private function smtpConnect()
    {
        if (is_null($this->smtp)) {
            $this->smtp = new SMTP();
        }
        $this->smtp->setTimeout($this->Timeout);
        $this->smtp->setDebugLevel($this->SMTPDebug);
        $this->smtp->setDebugOutput($this->Debugoutput);
        $this->smtp->setVerp($this->do_verp);
        
        $hosts = explode(';', $this->Host);
        foreach ($hosts as $hostentry) {
            $hostinfo = [];
            if (!preg_match('/^((ssl|tls):\/\/)?(.+?)(?::(\d+))?$/', trim($hostentry), $hostinfo)) {
                continue;
            }
            $prefix = '';
            $tls = false;
            if ('ssl' === $hostinfo[1] || ('' === $hostinfo[1] && 'ssl' === $this->SMTPSecure)) {
                $prefix = 'ssl://';
                $tls = false;
            } elseif ('tls' === $hostinfo[1]) {
                $tls = true;
            }
            $host = $hostinfo[3];
            $port = $this->Port;
            if (isset($hostinfo[4]) && is_numeric($hostinfo[4])) {
                $port = (int)$hostinfo[4];
            }
            if ($this->smtp->connect($prefix . $host, $port, $this->Timeout)) {
                try {
                    $hello = $this->serverHostname();
                    $this->smtp->hello($hello);
                    if ($tls) {
                        if (!$this->smtp->startTLS()) {
                            throw new Exception('Failed to start TLS');
                        }
                        $this->smtp->hello($hello);
                    }
                    if ($this->SMTPAuth && !$this->smtp->authenticate(
                        $this->Username,
                        $this->Password,
                        $this->AuthType,
                        $this->oauth
                    )) {
                        throw new Exception('SMTP authentication failed');
                    }
                    return true;
                } catch (Exception $exc) {
                    $this->smtp->quit();
                }
            }
        }
        $this->smtp->close();
        throw new Exception('SMTP connect() failed.');
    }
    
    private function smtpClose()
    {
        if (!is_null($this->smtp) && $this->smtp->connected()) {
            $this->smtp->quit();
            $this->smtp->close();
        }
    }
    
    private function createHeader()
    {
        $header = "From: {$this->FromName} <{$this->From}>\r\n";
        $header .= "To: {$this->recipient}\r\n";
        $header .= "Subject: {$this->Subject}\r\n";
        $header .= "Date: " . date('r') . "\r\n";
        $header .= "MIME-Version: 1.0\r\n";
        $header .= "Content-Type: {$this->ContentType}; charset={$this->CharSet}\r\n";
        $header .= "Content-Transfer-Encoding: {$this->Encoding}\r\n";
        return $header;
    }
    
    private function serverHostname()
    {
        $result = 'localhost.localdomain';
        if (!empty($this->Hostname)) {
            $result = $this->Hostname;
        } elseif (isset($_SERVER['SERVER_NAME'])) {
            $result = $_SERVER['SERVER_NAME'];
        } elseif (function_exists('gethostname') && gethostname() !== false) {
            $result = gethostname();
        } elseif (php_uname('n') !== false) {
            $result = php_uname('n');
        }
        return $result;
    }
}